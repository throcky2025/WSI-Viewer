import os
import subprocess
import sys
import time
from pathlib import Path
import shutil
import logging
from typing import Optional, Union

class WSIViewer:
    def __init__(self, host: str = "0.0.0.0", 
                 backend_port: int = 5000,
                 frontend_port: int = 3000,
                 static_dir: Optional[Union[str, Path]] = None,
                 log_level: str = "info"):
        """
        初始化WSI查看器
        
        Args:
            host: 服务器主机地址
            backend_port: 后端服务端口
            frontend_port: 前端服务端口
            static_dir: 静态文件目录路径
            log_level: 日志级别
        """
        # 配置日志
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        self.host = host
        self.backend_port = backend_port
        self.frontend_port = frontend_port
        self.project_root = Path(__file__).resolve().parent
        self.frontend_dir = self.project_root / "frontend"
        self.api_dir = self.project_root / "api"
        self.static_dir = Path(static_dir) if static_dir else self.project_root / "static"
        self.npm_path = None
        self.backend_process = None
        self.frontend_process = None

    def install_dependencies(self) -> bool:
        """安装必要的Python依赖"""
        self.logger.info("安装Python依赖...")
        requirements_path = self.project_root / "requirements-vis.txt"
        if requirements_path.exists():
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
                    check=True
                )
                self.logger.info("依赖安装完成")
                return True
            except subprocess.CalledProcessError as e:
                self.logger.error(f"依赖安装失败: {e}")
                return False
        else:
            self.logger.error(f"未找到requirements文件: {requirements_path}")
            return False

    def find_npm(self) -> Optional[str]:
        """查找npm可执行文件的路径"""
        if sys.platform == "win32":
            npm_paths = [
                shutil.which("npm"),
                r"C:\Program Files\nodejs\npm.cmd",
                r"C:\Program Files (x86)\nodejs\npm.cmd",
                os.path.expandvars(r"%APPDATA%\npm\npm.cmd"),
                os.path.expandvars(r"%ProgramFiles%\nodejs\npm.cmd"),
                os.path.expandvars(r"%ProgramFiles(x86)%\nodejs\npm.cmd"),
            ]
        else:
            npm_paths = [
                shutil.which("npm"),
                "/usr/local/bin/npm",
                "/usr/bin/npm",
            ]
        
        for path in npm_paths:
            if path and os.path.exists(path):
                return path
        return None

    def check_npm(self) -> Union[str, bool]:
        """检查并验证npm安装"""
        self.logger.info("检查npm安装...")
        npm_path = self.find_npm()
        
        if not npm_path:
            self.logger.error("未找到npm，请先安装Node.js")
            print("\n安装步骤：")
            print("1. 访问 https://nodejs.org/")
            print("2. 下载并安装Node.js（建议使用LTS版本）")
            print("3. 安装完成后重新运行此脚本")
            return False
        
        try:
            self.logger.info(f"使用npm路径: {npm_path}")
            result = subprocess.run([npm_path, "--version"], 
                                capture_output=True, 
                                text=True,
                                check=True)
            self.logger.info(f"检测到npm版本: {result.stdout.strip()}")
            return npm_path
        except Exception as e:
            self.logger.error(f"npm检查失败: {e}")
            return False

    def start_backend(self) -> bool:
        """启动FastAPI后端服务"""
        self.logger.info("启动后端服务...")
        if not self.api_dir.exists():
            self.logger.error(f"未找到API目录: {self.api_dir}")
            return False
        
        api_dir_str = str(self.api_dir)
        if api_dir_str not in sys.path:
            sys.path.insert(0, api_dir_str)
            
        env = os.environ.copy()
        env["PYTHONPATH"] = api_dir_str + os.pathsep + env.get("PYTHONPATH", "")
        
        try:
            self.backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", 
                "api.main:app", 
                "--host", self.host,
                "--port", str(self.backend_port),
                "--ws", "websockets",
                "--log-level", "info"],
                cwd=str(self.project_root),
                env=env
            )
            time.sleep(2)  # 等待服务启动
            self.logger.info("后端服务启动完成")
            return True
        except Exception as e:
            self.logger.error(f"后端服务启动失败: {e}")
            return False

    def start_frontend(self) -> bool:
        """启动Vue.js前端开发服务器"""
        if not self.frontend_dir.exists():
            self.logger.error(f"未找到前端目录: {self.frontend_dir}")
            return False
            
        try:
            self.frontend_process = subprocess.Popen(
                [self.npm_path, "run", "dev"],
                cwd=str(self.frontend_dir)
            )
            self.logger.info("前端服务启动完成")
            return True
        except Exception as e:
            self.logger.error(f"前端服务启动失败: {e}")
            return False

    def install_frontend_deps(self) -> bool:
        """安装前端依赖"""
        self.logger.info("安装前端依赖...")
        if not self.frontend_dir.exists():
            self.logger.error(f"未找到前端目录: {self.frontend_dir}")
            return False
        
        try:
            subprocess.run(
                [self.npm_path, "install"],
                check=True,
                cwd=str(self.frontend_dir)
            )
            self.logger.info("前端依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"前端依赖安装失败: {e}")
            return False

    def setup(self) -> bool:
        """设置服务环境"""
        self.logger.info("正在设置WSI查看器环境...")
        
        # 安装Python依赖
        if not self.install_dependencies():
            return False
            
        # 检查npm
        npm_path = self.check_npm()
        if not npm_path:
            return False
        self.npm_path = npm_path
            
        # 检查并安装前端依赖
        if not (self.frontend_dir / "node_modules").exists():
            if not self.install_frontend_deps():
                return False

        # 创建必要的目录
        self.static_dir.mkdir(exist_ok=True)
        (self.static_dir / "slides").mkdir(exist_ok=True)
        (self.static_dir / "frontend").mkdir(exist_ok=True)
        
        return True

    def start(self) -> None:
        """启动WSI查看器服务"""
        if not self.setup():
            self.logger.error("环境设置失败")
            return
        
        if not self.start_backend():
            self.logger.error("后端服务启动失败")
            return
            
        if not self.start_frontend():
            self.logger.error("前端服务启动失败")
            self.stop()
            return
        
        self.logger.info(f"\n服务启动成功！")
        self.logger.info(f"请在浏览器中访问：http://localhost:{self.frontend_port}")
        
        try:
            while True:
                if self.backend_process.poll() is not None:
                    self.logger.error("后端服务意外退出")
                    break
                if self.frontend_process.poll() is not None:
                    self.logger.error("前端服务意外退出")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("\n正在关闭服务...")
        finally:
            self.stop()

    def stop(self) -> None:
        """停止所有服务"""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
            
        self.logger.info("服务已停止")