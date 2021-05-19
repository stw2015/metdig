# _*_ coding: utf-8 _*_

# Copyright (c) 2019 NMC Developers.
# Distributed under the terms of the GPL V3 License.

"""
Read configure file.
"""

import os
import datetime
import shutil
import configparser
from pathlib import Path
import fnmatch
import re


def _get_config_dir():
    """
    Get default configuration directory.
    """
    config_dir = Path.home() / ".metdig"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


# Global Variables
CONFIG_DIR = _get_config_dir()


def _ConfigFetchError(Exception):
    pass


def _get_config_from_rcfile():
    """
    Get configure information from config_dk_met_io.ini file.
    """
    rc = CONFIG_DIR / "config.ini"
    if not rc.is_file():
        rc = Path("~/config_met_io.ini").expanduser()
    try:
        config = configparser.ConfigParser()
        config.read(rc)
    except IOError as e:
        raise _ConfigFetchError(str(e))
    except Exception as e:
        raise _ConfigFetchError(str(e))

    return config


# Global Variables
CONFIG = _get_config_from_rcfile()

warn_era5tag = True


def get_cache_dir():
    # get cache file directory
    if CONFIG.has_option('CACHE', 'CACHE_DIR'):
        cache_dir = Path(CONFIG['CACHE']['CACHE_DIR']).expanduser() / "cache"
    else:
        cache_dir = CONFIG_DIR / "cache"
    return cache_dir


def get_era5cache_file(init_time, var_name, extent, level=None, find_area=True):
    """[获取era5缓存数据文件路径]

    Args:
        init_time ([datetime]): [世界时时间]
        var_name ([str]): [stda要素名]
        extent ([tuple]): [数据区域]
        level ([int], optional): [层次]. Defaults to None.
        find_area (bool, optional): [是否区域查询]. Defaults to True.

    Returns:
        [type]: [description]
    """    

    # get cache file directory
    if CONFIG.has_option('CACHE', 'CACHE_DIR'):
        cache_dir = Path(CONFIG['CACHE']['CACHE_DIR']).expanduser() / "cache"
    else:
        cache_dir = CONFIG_DIR / "cache"

    cache_dir = cache_dir / 'ERA5_DATA'

    # print usrinfo
    global warn_era5tag
    if warn_era5tag:
        warn_era5tag = False
        warn_msg = '当前ERA5_DATA缓存目录为：{}， 请用户自行注意磁盘使用空间，必要时请手动清理或更改缓存目录！'.format(cache_dir)
        print(warn_msg)

    if level:
        cache_dir = cache_dir / '{:%Y%m%d%H%M}/hourly/{}/{}'.format(init_time, var_name, level)
    else:
        cache_dir = cache_dir / '{:%Y%m%d%H%M}/hourly/{}'.format(init_time, var_name)

    # search match area file
    cache_file = cache_dir / '{:%Y%m%d%H%M}_{}_{}_{}_{}.nc'.format(init_time, extent[0], extent[1], extent[2], extent[3])

    if find_area and os.path.exists(cache_dir):
        filefmt = '{:%Y%m%d%H%M}_*.nc'.format(init_time)
        fnames = fnmatch.filter(os.listdir(cache_dir), filefmt)
        if fnames:
            for name in fnames:
                # such as name = '202007250800_28_180_-7_77.nc', file_extent = ['202007250800', '28', '180', '-7', '77']
                file_extent = re.findall(r"\-?\d+\.?\d*", os.path.splitext(name)[0])
                if len(file_extent) == 5:
                    file_extent = float(file_extent[1]), float(file_extent[2]), float(file_extent[3]), float(file_extent[4])
                    if file_extent[0] <= extent[0] and file_extent[1] >= extent[1] and file_extent[2] <= extent[2] and file_extent[3] >= extent[3]:
                        cache_file = cache_dir / name
                        break

    return cache_file