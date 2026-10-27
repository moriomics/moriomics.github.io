import os
import sys
import time

def fake_worker(connection, cancel, kind, payload, temporary_dir):
    if sys.platform != 'win32':
        os.setsid()
    try:
        if kind == 'probe':
            connection.send(('result', {'duration_seconds': 2.0, 'size_bytes': 64, 'audio_index': 0}))
        elif kind == 'transcribe':
            if 'bad' in payload['project']['source_path']:
                connection.send(('error', {'message': 'テスト用の失敗', 'code': 'TestFailure'}))
                return
            p = payload['project']
            seg = {'id': 0, 'start': 0.0, 'end': 1.0, 'raw_text': '認識した文章', 'edited_text': None}
            connection.send(('segment', seg))
            p['segments'], p['status'] = [seg], '完了'
            connection.send(('result', p))
        elif kind == 'slow':
            connection.send(('stage', '認識中'))
            while not cancel.is_set():
                time.sleep(.02)
            connection.send(('cancelled', None))
        elif kind == 'stuck':
            connection.send(('stage', '認識中'))
            while True:
                time.sleep(.02)
    finally:
        connection.close()
