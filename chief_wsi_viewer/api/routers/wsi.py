from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import sys
from typing import Optional
from ..services.wsi_service import WSIService
import uuid
import os

# 创建路由器
router = APIRouter()

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 添加控制台处理器
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 配置WSI文件存储路径
UPLOAD_DIR = Path("static/slides")
CACHE_DIR = Path("static/tiles")

# 确保目录存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# 初始化WSI服务
wsi_service = WSIService(cache_dir=str(CACHE_DIR))

@router.post("/upload")
async def upload_slide(file: UploadFile = File(...)):
    """上传WSI切片文件"""
    logger.debug(f"开始处理文件上传: {file.filename}")
    
    try:
        # 生成唯一文件名
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        logger.debug(f"保存文件到: {file_path}")
        
        # 保存文件
        try:
            content = await file.read()
            if len(content) == 0:
                raise ValueError("文件内容为空")
            
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"文件已保存: {file_path} (大小: {file_size} 字节)")
            
        except Exception as e:
            logger.error(f"保存文件失败: {str(e)}")
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500,
                detail=f"保存文件失败: {str(e)}"
            )
        
        # 验证文件
        try:
            success, info = wsi_service.open_slide(str(file_path))
            
            if not success:
                logger.error("文件验证失败")
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(
                    status_code=400,
                    detail="无效的图像文件"
                )
            
            logger.info(f"图像信息: {info}")
            return {
                "success": True,
                "slideId": unique_filename,
                "info": info
            }
            
        except Exception as e:
            logger.error(f"验证文件失败: {str(e)}")
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=400,
                detail=f"无效的图像文件: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/{slide_id}/info")
async def get_slide_info(slide_id: str):
    """获取WSI切片信息"""
    logger.debug(f"请求切片信息: {slide_id}")
    
    try:
        file_path = UPLOAD_DIR / slide_id
        if not file_path.exists():
            logger.error(f"切片文件未找到: {file_path}")
            raise HTTPException(
                status_code=404,
                detail="切片文件未找到"
            )
            
        success, info = wsi_service.open_slide(str(file_path))
        if not success:
            logger.error(f"无法打开切片文件: {file_path}")
            raise HTTPException(
                status_code=500,
                detail="无法打开切片文件"
            )
            
        logger.debug(f"返回切片信息: {info}")
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取切片信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取切片信息失败: {str(e)}"
        )

@router.get("/{slide_id}/tile")
async def get_slide_tile(
    slide_id: str,
    x: int = Query(..., description="Tile X坐标"),
    y: int = Query(..., description="Tile Y坐标"),
    level: int = Query(..., description="缩放级别"),
    size: int = Query(256, description="Tile大小")
):
    """获取WSI切片的指定区域图像"""
    logger.debug(f"请求tile: slide_id={slide_id}, x={x}, y={y}, level={level}, size={size}")
    
    try:
        file_path = UPLOAD_DIR / slide_id
        if not file_path.exists():
            logger.error(f"切片文件未找到: {file_path}")
            raise HTTPException(
                status_code=404,
                detail="切片文件未找到"
            )
            
        # 获取tile
        tile_path = wsi_service.get_tile(str(file_path), x, y, level, size)
        
        if tile_path is None:
            logger.error(f"无法获取tile: x={x}, y={y}, level={level}")
            raise HTTPException(
                status_code=404,
                detail="无法获取请求的tile"
            )
            
        logger.debug(f"返回tile: {tile_path}")
        return FileResponse(tile_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取tile失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取tile失败: {str(e)}"
        )

@router.delete("/{slide_id}")
async def delete_slide(slide_id: str):
    """删除WSI切片文件"""
    logger.debug(f"请求删除切片: {slide_id}")
    
    try:
        file_path = UPLOAD_DIR / slide_id
        if not file_path.exists():
            logger.error(f"切片文件未找到: {file_path}")
            raise HTTPException(
                status_code=404,
                detail="切片文件未找到"
            )
            
        # 删除原始文件
        file_path.unlink()
        logger.info(f"已删除切片文件: {file_path}")
        
        # 清理相关的缓存文件
        try:
            cache_pattern = f"{Path(slide_id).stem}_*"
            for cache_file in CACHE_DIR.glob(cache_pattern):
                cache_file.unlink()
                logger.debug(f"已删除缓存文件: {cache_file}")
        except Exception as e:
            logger.warning(f"清理缓存文件失败: {str(e)}")
            
        return {"success": True, "message": "文件已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除文件失败: {str(e)}"
        )