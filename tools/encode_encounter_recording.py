"""Fully decode runtime PNG frames and encoded MP4 before allowing the waiting editor to quit."""
from pathlib import Path
import sys,json,subprocess,hashlib,statistics,math
from array import array
out=Path(sys.argv[1]).resolve();r=json.loads((out/'recording-ready.json').read_text());frames=r['frames'];lines=['ffconcat version 1.0']
for i,frame in enumerate(frames):
    path=Path(frame['path']);assert path.is_relative_to(out);assert hashlib.sha256(path.read_bytes()).hexdigest()==frame['sha256']
    lines.append("file '"+path.as_posix()+"'");duration=frames[i+1]['wall_time']-frame['wall_time'] if i+1<len(frames) else .12;lines.append('duration '+str(max(.001,duration)))
concat=out/'frames.ffconcat';concat.write_text('\n'.join(lines)+'\n')
movie=out/'TeddyEncounter-gameplay.mp4';assert not movie.exists()
audio_samples=array('f');audio_samples.frombytes(subprocess.check_output(['ffmpeg','-v','error','-xerror','-i',str(out/'gameplay-audio.wav'),'-f','f32le','-acodec','pcm_f32le','-']))
audio_peak=max(abs(x) for x in audio_samples)
audio_present=audio_peak>0.000001
args=['ffmpeg','-v','error','-xerror','-f','concat','-safe','0','-i',str(concat)]
if audio_present:args+=['-i',str(out/'gameplay-audio.wav')]
args+=['-vf','fps=30','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p']
args+=['-c:a','aac','-ac','2','-b:a','160k','-shortest'] if audio_present else ['-an']
args+=['-movflags','+faststart',str(movie)]
subprocess.run(args,check=True)
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'],check=True)
metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(movie)]))
delta=[b['wall_time']-a['wall_time'] for a,b in zip(frames,frames[1:])]
receipt={'passed':True,'movie':str(movie),'sha256':hashlib.sha256(movie.read_bytes()).hexdigest(),'source_frames':len(frames),'source_png_full_decode':'FFmpeg decoded every input frame with -xerror during encoding','encoded_full_decode':True,'capture_interval_median_seconds':statistics.median(delta),'capture_interval_max_seconds':max(delta),'output_fps':30,'resampling':'Frame duplication from actual wall-clock capture intervals; 30 fps container is not a claim of 30 unique source frames per second','audio_included':audio_present,'audio_peak_linear':audio_peak,'audio_note':'Recorded master output included' if audio_present else 'Offscreen PIE master output was silent; silent track omitted. Native game audio separately verified. No replacement or dubbed audio.','metadata':metadata,'arguments':args}
(out/'encoded.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items() if k not in ['metadata','arguments']},indent=2))
