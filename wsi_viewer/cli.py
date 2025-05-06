import argparse
from .viewer import WSIViewer

def main():
    parser = argparse.ArgumentParser(description='CHIEF WSI查看器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--backend-port', type=int, default=5000, help='后端服务端口')
    parser.add_argument('--frontend-port', type=int, default=3000, help='前端服务端口')
    parser.add_argument('--static-dir', help='静态文件目录路径')
    parser.add_argument('--log-level', default='info', 
                       choices=['debug', 'info', 'warning', 'error'],
                       help='日志级别')

    args = parser.parse_args()
    
    viewer = WSIViewer(
        host=args.host,
        backend_port=args.backend_port,
        frontend_port=args.frontend_port,
        static_dir=args.static_dir,
        log_level=args.log_level
    )
    viewer.start()

if __name__ == '__main__':
    main()