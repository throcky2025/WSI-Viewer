from pathlib import Path
import numpy as np
from PIL import Image
import logging
import cv2
from typing import Dict, Tuple, Optional
import os
import math
import time

logger = logging.getLogger(__name__)

class WSIService:
    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir)
        self.slides = {}
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def open_slide(self, slide_path: str) -> Tuple[bool, Optional[Dict]]:
        try:
            if not os.path.exists(slide_path):
                logger.error(f"文件不存在: {slide_path}")
                return False, None

            # 读取原始图像
            img = cv2.imread(str(slide_path))
            if img is None:
                logger.error(f"无法读取图像: {slide_path}")
                return False, None
                
            # 转换为RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 获取图像尺寸
            height, width = img.shape[:2]
            logger.info(f"原始图像尺寸: {width}x{height}")
            
            # 计算金字塔层级数
            max_dimension = max(width, height)
            min_dimension = 256  # 最小的tile尺寸
            level_count = math.ceil(math.log2(max_dimension / min_dimension)) + 1
            
            # 生成金字塔层级信息
            level_dimensions = []
            level_downsamples = []
            current_width = width
            current_height = height
            
            for level in range(level_count):
                level_dimensions.append((current_width, current_height))
                level_downsamples.append(math.pow(2, level))
                
                # 计算下一级别的尺寸
                current_width = max(current_width // 2, 256)
                current_height = max(current_height // 2, 256)
                
            logger.info(f"生成{level_count}个层级:")
            for i, (w, h) in enumerate(level_dimensions):
                logger.info(f"Level {i}: {w}x{h}, 缩放比例: {level_downsamples[i]}")
                
            # 创建信息字典
            info = {
                'dimensions': (width, height),
                'level_count': level_count,
                'level_dimensions': level_dimensions,
                'level_downsamples': level_downsamples,
                'properties': {
                    'openslide.level-count': str(level_count),
                    'openslide.mpp-x': '0.2508',
                    'openslide.mpp-y': '0.2508',
                    'tiff.width': str(width),
                    'tiff.height': str(height)
                },
                'format': 'tiff'
            }
            
            # 生成金字塔缓存
            pyramid = []
            current_image = img
            for i, (target_w, target_h) in enumerate(level_dimensions):
                if i == 0:
                    pyramid.append(current_image)
                else:
                    resized = cv2.resize(current_image, (target_w, target_h), 
                                       interpolation=cv2.INTER_AREA)
                    pyramid.append(resized)
                    current_image = resized
                    
            self.slides[slide_path] = {
                'pyramid': pyramid,
                'info': info
            }
            
            logger.info(f"成功打开图像文件: {slide_path}")
            return True, info
                
        except Exception as e:
            logger.error(f"打开图像失败: {str(e)}")
            return False, None

    def get_tile(self, 
                 slide_path: str, 
                 x: int, 
                 y: int, 
                 level: int, 
                 size: int = 256) -> Optional[str]:
        """获取指定位置的tile"""
        try:
            # 生成缓存文件名
            slide_id = Path(slide_path).stem
            cache_file = self.cache_dir / f"{slide_id}_{level}_{x}_{y}_{size}.jpg"
            logger.debug(f'请求tile: path={slide_path}, x={x}, y={y}, level={level}')
            
            # 检查缓存
            if cache_file.exists():
                logger.debug(f'使用缓存: {cache_file}')
                return str(cache_file)
            
            # 获取切片信息
            slide_info = self.slides.get(slide_path)
            if not slide_info:
                success, info = self.open_slide(slide_path)
                if not success:
                    return None
                slide_info = self.slides[slide_path]
            
            # 获取对应level的图像
            pyramid = slide_info['pyramid']
            if level >= len(pyramid):
                logger.error(f'无效的level: {level}, 最大level: {len(pyramid)-1}')
                return None
            
            # 获取当前level的图像和尺寸信息
            level_image = pyramid[level]
            level_width, level_height = level_image.shape[1], level_image.shape[0]
            
            # 计算tile范围
            tile_x = x * size
            tile_y = y * size
            end_x = min(tile_x + size, level_width)
            end_y = min(tile_y + size, level_height)
            
            # 检查范围是否有效
            if tile_x >= level_width or tile_y >= level_height:
                logger.error(f'tile坐标超出范围: x={tile_x}/{level_width}, y={tile_y}/{level_height}')
                return None
                
            # 提取tile区域
            tile = level_image[tile_y:end_y, tile_x:end_x]
            
            # 处理边缘tile的填充
            if tile.shape[0] != size or tile.shape[1] != size:
                logger.debug(f'填充tile边缘: 从{tile.shape}到{size}x{size}')
                full_tile = np.full((size, size, 3), 255, dtype=np.uint8)
                full_tile[:tile.shape[0], :tile.shape[1]] = tile
                tile = full_tile
            
            # 保存为JPEG
            cv2.imwrite(str(cache_file), cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))
            logger.debug(f'保存tile: {cache_file}')
            
            return str(cache_file)
            
        except Exception as e:
            logger.error(f'获取tile失败: {str(e)}')
            return None

    def cleanup(self):
        """清理资源"""
        self.slides.clear()