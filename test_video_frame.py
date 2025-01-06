import cv2
import numpy as np
import tempfile
import os
import requests
import base64
from PIL import Image
import io
import ffmpeg
import time

def get_first_frame(video_url: str, chunk_size: int = 1024 * 1024) -> str | None:
    """使用ffmpeg获取视频第一帧（快速方法，只下载部分数据）"""
    temp_file = None
    temp_frame = None
    result = None
    
    try:
        print("开始获取视频信息...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 获取视频总大小
        response = requests.head(video_url, headers=headers)
        total_size = int(response.headers.get('content-length', 0))
        if total_size == 0:
            print("无法获取视频大小")
            return None
            
        print(f"视频总大小: {total_size / 1024 / 1024:.2f}MB")
        
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_frame = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        temp_frame_path = temp_frame.name
        temp_frame.close()  # 立即关闭临时帧文件
        
        # 先下载末尾部分
        print("下载视频尾部数据...")
        headers['Range'] = f'bytes={max(0, total_size - chunk_size)}-{total_size-1}'
        response = requests.get(video_url, headers=headers, stream=True)
        
        if response.status_code not in [200, 206]:
            print(f"下载失败，状态码: {response.status_code}")
            return None
            
        # 获取实际下载的大小
        content_length = int(response.headers.get('content-length', 0))
        print(f"尾部数据大小: {content_length / 1024 / 1024:.2f}MB")
        
        # 将文件指针移到对应位置
        temp_file.seek(max(0, total_size - chunk_size))
            
        downloaded_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                downloaded_size += len(chunk)
                print(f"\r下载进度: {downloaded_size / content_length * 100:.2f}%", end='')
        
        # 下载开头部分
        print("\n下载视频头部数据...")
        headers['Range'] = f'bytes=0-{chunk_size-1}'
        response = requests.get(video_url, headers=headers, stream=True)
        
        if response.status_code not in [200, 206]:
            print(f"下载失败，状态码: {response.status_code}")
            return None
            
        # 获取实际下载的大小
        content_length = int(response.headers.get('content-length', 0))
        print(f"头部数据大小: {content_length / 1024 / 1024:.2f}MB")
        
        # 将文件指针移到开头
        temp_file.seek(0)
            
        downloaded_size = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)
                downloaded_size += len(chunk)
                print(f"\r下载进度: {downloaded_size / content_length * 100:.2f}%", end='')
        
        print("\n下载完成")
        temp_file.flush()
        temp_file_path = temp_file.name
        temp_file.close()  # 关闭临时视频文件
            
        print("开始使用ffmpeg提取第一帧...")
        try:
            # 使用更多的ffmpeg参数来处理视频
            stream = ffmpeg.input(temp_file_path)
            stream = ffmpeg.output(stream, temp_frame_path,
                                 vframes=1,
                                 f='image2',  # 强制使用图片格式
                                 vcodec='mjpeg',  # 使用JPEG编码器
                                 loglevel='error'  # 只显示错误信息
                                )
            print("执行ffmpeg命令...")
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
            
            # 等待文件写入完成
            time.sleep(0.1)
            
            if not os.path.exists(temp_frame_path) or os.path.getsize(temp_frame_path) == 0:
                raise Exception("输出文件不存在或为空")
                
            print("成功获取第一帧")
            # 读取图片并转换为base64
            with open(temp_frame_path, 'rb') as f:
                img_data = f.read()
                result = f"data:image/jpeg;base64,{base64.b64encode(img_data).decode()}"
            
            # 保存帧为图片文件
            import shutil
            shutil.copy(temp_frame_path, 'first_frame.jpg')
            print("已保存帧为 first_frame.jpg")
            
            # 保存base64字符串到文件
            with open('frame_base64.txt', 'w') as f:
                f.write(result)
            print("已保存base64编码到 frame_base64.txt")
            
            return result
            
        except ffmpeg.Error as e:
            print(f"ffmpeg错误: {e.stderr.decode()}")
            if chunk_size < 8 * 1024 * 1024:  # 如果数据不够，尝试下载更多
                print(f"尝试下载更多数据...")
                return get_first_frame(video_url, chunk_size * 2)
            return None
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None
    finally:
        # 确保文件句柄已关闭
        if temp_file and not temp_file.closed:
            temp_file.close()
        if temp_frame and not temp_frame.closed:
            temp_frame.close()
            
        # 等待一小段时间确保文件不再被占用
        time.sleep(0.1)
        
        # 清理临时文件
        try:
            if temp_file:
                os.unlink(temp_file.name)
        except Exception as e:
            print(f"清理临时视频文件时发生错误: {str(e)}")
            
        try:
            if temp_frame:
                os.unlink(temp_frame.name)
        except Exception as e:
            print(f"清理临时帧文件时发生错误: {str(e)}")
            
        return result

if __name__ == "__main__":
    # 在这里替换你的视频URL
    video_url = "https://sns-video-bd.xhscdn.com/pre_post/1040g2t031c1m9mq1gk8049c0589cn1su3lc7o90"
    
    print(f"测试URL: {video_url}")
    result = get_first_frame(video_url)
    
    if result:
        print("\n处理成功！")
        print(f"Base64字符串长度: {len(result)}")
    else:
        print("\n处理失败！") 