"""Local-only static research viewer with byte ranges for video seeking."""
import argparse,os,re
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8792);a=p.parse_args()
root=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Accept-Ranges','bytes');super().end_headers()
    def send_head(self):
        self.byte_range=None
        path=Path(self.translate_path(self.path));header=self.headers.get('Range')
        if not header or not path.is_file():return super().send_head()
        size=path.stat().st_size;match=re.fullmatch(r'bytes=(\d*)-(\d*)',header.strip())
        if not match or not any(match.groups()):self.send_error(416);return None
        first,last=match.groups()
        start=int(first) if first else max(0,size-int(last))
        end=min(int(last),size-1) if first and last else size-1
        if start>=size or end<start:
            self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.send_header('Content-Length','0');self.end_headers();return None
        f=path.open('rb');f.seek(start);self.byte_range=(start,end)
        self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Content-Length',str(end-start+1));self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Last-Modified',self.date_time_string(path.stat().st_mtime));self.end_headers();return f
    def copyfile(self,source,output):
        if self.byte_range is None:return super().copyfile(source,output)
        remaining=self.byte_range[1]-self.byte_range[0]+1
        try:
            while remaining:
                data=source.read(min(1024*1024,remaining))
                if not data:break
                output.write(data);remaining-=len(data)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):pass
ThreadingHTTPServer(('127.0.0.1',a.port),partial(Handler,directory=str(root))).serve_forever()
