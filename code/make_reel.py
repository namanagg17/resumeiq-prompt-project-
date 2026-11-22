"""Cuts docs/reel/raw.webm into segments, burns captions, adds title cards, writes docs/reel/ResumeIQ_reel.mp4.
Plan in docs/reel/plan.json: list of {"card": name, "seconds": n} or {"from": mark, "to": mark, "offset_from": s,
"offset_to": s, "speed": x, "captions": [[text, start, end], ...]} (caption times relative to the segment)."""
import json, subprocess, os
R = "../docs/reel"
marks = json.load(open(f"{R}/marks.json"))
plan = json.load(open(f"{R}/plan.json"))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
parts = []
for i, step in enumerate(plan):
    out = f"{R}/part_{i:02d}.mp4"
    if "card" in step:
        cmd = ["ffmpeg", "-y", "-loop", "1", "-t", str(step["seconds"]), "-i", f"{R}/card_{step['card']}.png",
               "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "fast", out]
    else:
        start = marks[step["from"]] + step.get("offset_from", 0)
        end = marks[step["to"]] + step.get("offset_to", 0)
        speed = step.get("speed", 1)
        filters = [f"setpts=PTS/{speed}" if speed != 1 else "null", "fps=30", "scale=1280:720"]
        for j, (text, a, b) in enumerate(step.get("captions", [])):
            tf = f"{R}/cap_{i}_{j}.txt"
            open(tf, "w").write(text)
            filters.append(f"drawtext=fontfile={FONT}:textfile={tf}:fontsize=26:fontcolor=white:box=1:boxcolor=black@0.78:"
                           f"boxborderw=14:x=(w-text_w)/2:y=h-text_h-36:line_spacing=6:enable='between(t,{a},{b})'")
        filters.append("format=yuv420p")
        cmd = ["ffmpeg", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", f"{R}/raw.webm", "-an",
               "-vf", ",".join(filters), "-c:v", "libx264", "-preset", "fast", out]
    subprocess.run(cmd, check=True, capture_output=True)
    parts.append(out)
with open(f"{R}/list.txt", "w") as f:
    f.writelines(f"file '{os.path.basename(p)}'\n" for p in parts)
final = f"{R}/ResumeIQ_reel.mp4"
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{R}/list.txt", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-shortest", "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart", final], check=True, capture_output=True)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip()
print("reel:", final, "duration:", dur, "s")
