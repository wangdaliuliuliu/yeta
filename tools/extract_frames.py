"""Extract frames from compact research videos with existing ffmpeg; no model/API needed."""
import argparse,gzip,json,subprocess,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description='从压缩研究视频按帧号或时间段提取画面，输出默认集中在本包frames目录。')
p.add_argument('id',help='视频ID');p.add_argument('--frame',type=int,help='单帧，编号从1开始')
p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float,default=2)
p.add_argument('--every',type=int,default=1,help='时间段内每多少原始帧提取一次，默认每帧')
a=p.parse_args()
if not a.id.isdigit() or a.every<1: p.error('ID必须是数字，every必须≥1')
video=BASE/'videos'/f'{a.id}.mp4';idx=BASE/'transcripts'/a.id/'source_timestamp_index.json.gz'
with gzip.open(idx,'rt',encoding='utf-8-sig') as f:frames=json.load(f)['frames']
if a.frame is not None:
    if not 1<=a.frame<=len(frames):p.error('帧号超出范围')
    selected=[frames[a.frame-1]];filter_expr=f'select=eq(n\\,{a.frame-1})'
    tag=f'frame_{a.frame:06d}'
else:
    if a.end<a.start:p.error('end必须≥start')
    candidates=[i for i,x in enumerate(frames) if a.start<=float(x['timestamp_seconds'])<=a.end]
    selected=[frames[i] for i in candidates[::a.every]]
    if not selected:p.error('所选时间段没有帧')
    lo=candidates[0];hi=candidates[-1]
    filter_expr=f'select=between(n\\,{lo}\\,{hi})*not(mod(n-{lo}\\,{a.every}))'
    tag=f'{a.start:g}s_{a.end:g}s_every{a.every}'
out=BASE/'frames'/a.id/tag;out.mkdir(parents=True,exist_ok=True)
cmd=['ffmpeg','-hide_banner','-loglevel','error','-i',str(video),'-vf',filter_expr,'-fps_mode','vfr','-frames:v',str(len(selected)),'-q:v','2','-y',str(out/'sample_%06d.jpg')]
subprocess.run(cmd,check=True)
images=sorted(out.glob('sample_*.jpg'))
if len(images)!=len(selected):raise RuntimeError('提取帧数与预期不一致')
manifest={'video':str(video),'note':'这些是有损压缩版视频的帧，不是未压缩源像素；帧号按保留的源顺序定位。','frames':[{'file':im.name,'source_frame_number':x['frame_number'],'source_timestamp_seconds':x['timestamp_seconds']} for im,x in zip(images,selected)]}
(out/'index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(str(out),len(images),'帧')
