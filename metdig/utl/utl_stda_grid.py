# -*- coding: utf-8 -*-

import datetime

import xarray as xr
import numpy as np
import pandas as pd
from metpy.units import units

import metdig.utl as mdgstda

__all__ = [
    'xrda_to_gridstda',
    'numpy_to_gridstda',  # 目前不建议用该接口（仍在优化中），改用用npda_to_gridstda
    'npda_to_gridstda',
    'gridstda_full_like',
    'gridstda_full_like_by_levels',
]


def xrda_to_gridstda(xrda,
                     member_dim='member', level_dim='level', time_dim='time', dtime_dim='dtime', lat_dim='lat', lon_dim='lon',
                     member=None, level=None, time=None, dtime=None, lat=None, lon=None,
                     np_input_units='', var_name='',
                     **attrs_kwargs):
    """[通过给出('member', 'level', 'time', 'dtime', 'lat', 'lon')在原始xrda中的维度名称，将xrda转成stda（如果不给出缺失的维度数据，默认填0）

    Example:
    xrda = xr.DataArray([[271, 272, 273], [274, 275, 276]], dims=("X", "Y"), coords={"X": [10, 20], 'Y': [80, 90, 100]})

    # 指定xrda中各个维度对应的stda的维度名称
    stda = metdig.utl.xrda_to_gridstda(xrda, lon_dim='X', lat_dim='Y') 

    # 可以指定缺失的stda维度
    stda = metdig.utl.xrda_to_gridstda(xrda, lon_dim='X', lat_dim='Y', member=['cassandra']) 

    # 可以指定stda的要素，同时给定输入单位，自动转换为stda的单位
    stda = metdig.utl.xrda_to_gridstda(xrda, lon_dim='X', lat_dim='Y', member=['cassandra'], np_input_units='K' ,var_name='tmp') 

    ]

    Args:
        xrda ([xarray.DataArray]): [输入的DataArray]
        member_dim (str, optional): [xrda中代表stda的member维的名称]. Defaults to 'member'.
        level_dim (str, optional): [xrda中代表stda的level维的名称]. Defaults to 'level'.
        time_dim (str, optional): [xrda中代表stda的time维的名称]. Defaults to 'time'.
        dtime_dim (str, optional): [xrda中代表stda的dtime维的名称]. Defaults to 'dtime'.
        lat_dim (str, optional): [xrda中代表stda的lat维的名称]. Defaults to 'lat'.
        lon_dim (str, optional): [xrda中代表stda的lon维的名称]. Defaults to 'lon'.
        member ([list], optional): [使用member替换xrda的member数据]]. Defaults to None.
        level ([list], optional): [使用level替换xrda的level数据]. Defaults to None.
        time ([list], optional): [使用time替换xrda的time数据]. Defaults to None.
        dtime ([list], optional): [使用dtime替换xrda的dtime数据]. Defaults to None.
        lat ([list], optional): [使用lat替换xrda的lat数据]. Defaults to None.
        lon ([list], optional): [使用lon替换xrda的lon数据]. Defaults to None.
        np_input_units (str, optional): [np_input数据对应的单位，自动转换为能查询到的stda单位]. Defaults to ''.
        var_name (str, optional): [要素名]. Defaults to ''.
        **attrs_kwargs {[type]} -- [其它相关属性，如：data_source='cassandra', level_type='high']

    Returns:
        [STDA] -- [STDA网格数据]
    """
    def _easy_check_None(parm):
        if parm is None:
            return True
        if len(parm) == 1 and parm[0] is None:
            return True
        return False

    stda_data = xrda.copy(deep=True)

    # 已知维度替换成stda维度名称，同时补齐缺失维度
    if member_dim in xrda.dims:
        stda_data = stda_data.rename({member_dim: 'member'})
    else:
        stda_data = stda_data.expand_dims(member=[0])
    if level_dim in xrda.dims:
        stda_data = stda_data.rename({level_dim: 'level'})
    else:
        stda_data = stda_data.expand_dims(level=[0])
    if time_dim in xrda.dims:
        stda_data = stda_data.rename({time_dim: 'time'})
    else:
        stda_data = stda_data.expand_dims(time=[0])
    if dtime_dim in xrda.dims:
        stda_data = stda_data.rename({dtime_dim: 'dtime'})
    else:
        stda_data = stda_data.expand_dims(dtime=[0])
    if lat_dim in xrda.dims:
        stda_data = stda_data.rename({lat_dim: 'lat'})
    else:
        stda_data = stda_data.expand_dims(lat=[0])
    if lon_dim in xrda.dims:
        stda_data = stda_data.rename({lon_dim: 'lon'})
    else:
        stda_data = stda_data.expand_dims(lon=[0])

    # 替换掉需要替换的维度数据
    if _easy_check_None(member) == False:
        stda_data = stda_data.assign_coords(member=member)
    if _easy_check_None(level) == False:
        stda_data = stda_data.assign_coords(level=level)
    if _easy_check_None(time) == False:
        stda_data = stda_data.assign_coords(time=time)
    if _easy_check_None(dtime) == False:
        stda_data = stda_data.assign_coords(dtime=dtime)
    if _easy_check_None(lat) == False:
        stda_data = stda_data.assign_coords(lat=lat)
    if _easy_check_None(lon) == False:
        stda_data = stda_data.assign_coords(lon=lon)

    # 转置到stda维度
    stda_data = stda_data.transpose('member', 'level', 'time', 'dtime', 'lat', 'lon')

    # delete 冗余维度
    stda_data = stda_data.drop([i for i in stda_data.coords if i not in stda_data.dims])

    # attrs
    stda_attrs = mdgstda.get_stda_attrs(var_name=var_name, **attrs_kwargs)
    # 单位转换
    stda_data.values, data_units = mdgstda.numpy_units_to_stda(stda_data.values, np_input_units, stda_attrs['var_units'])
    stda_attrs['var_units'] = data_units
    stda_data.attrs = stda_attrs

    return stda_data


def npda_to_gridstda(npda,
                     dims=('lat', 'lon'),
                     member=None, level=None, time=None, dtime=None, lat=None, lon=None,
                     np_input_units='', var_name='',
                     **attrs_kwargs):
    """[通过给出npda的维度信息及其维度数据，('member', 'level', 'time', 'dtime', 'lat', 'lon')，将npda转成stda（如果不给出缺失的维度数据，默认填0）
    Example:
    npda = np.array([[271, 272, 273], [274, 275, 276]])

    # 指定xrda中各个维度对应的stda的维度名称
    stda = metdig.utl.npda_to_gridstda(npda, dims=('lat', 'lon'), lon=[80, 90, 100], lat=[10, 20])

    # 可以指定缺失的stda维度
    stda = metdig.utl.npda_to_gridstda(npda, dims=('lat', 'lon'), lon=[80, 90, 100], lat=[10, 20], member=['cassandra'])

    # 可以指定stda的要素，同时给定输入单位，自动转换为stda的单位
    stda =  metdig.utl.npda_to_gridstda(npda, dims=('lat', 'lon'), lon=[80, 90, 100], lat=[10, 20], member=['cassandra'], np_input_units='K' ,var_name='tmp') 

    ]

    Args:
        npda ([ndarray]): [numpy数据]
        dims (tuple, optional): [npda对应的stda的维度]. Defaults to ('lat', 'lon').
        member ([list], optional): [npda的member维数据]]. Defaults to None.
        level ([list], optional): [npda的level维数据]. Defaults to None.
        time ([list], optional): [npda的time维数据]. Defaults to None.
        dtime ([list], optional): [npda的dtime维数据]. Defaults to None.
        lat ([list], optional): [npda的lat维数据]. Defaults to None.
        lon ([list], optional): [npda的lon维数据]. Defaults to None.
        np_input_units (str, optional): [np_input数据对应的单位，自动转换为能查询到的stda单位]. Defaults to ''.
        var_name (str, optional): [要素名]. Defaults to ''.
        **attrs_kwargs {[type]} -- [其它相关属性，如：data_source='cassandra', level_type='high']

    Returns:
        [STDA] -- [STDA网格数据]
    """
    if len(npda.shape) != len(dims):
        raise Exception('error: npda shape not equal dims, please check npda and dims')
    for _d in dims:
        if _d != 'member' and _d != 'level' and _d != 'time' and _d != 'dtime' and _d != 'lat' and _d != 'lon':
            raise Exception('''error: dims need the following definitions: ('member', 'level', 'time', 'dtime', 'lat', 'lon'), please check dims''')

    temp = dict(member=member, level=level, time=time, dtime=dtime, lat=lat, lon=lon)

    # 第一步：输入的npda转成xrda
    coords = [(_d,  np.arange(_l)) if temp[_d] is None else (_d,  temp[_d]) for _d, _l in zip(dims, npda.shape)]
    xrda = xr.DataArray(npda, coords=coords)

    # 第二步：缺失维度补齐，未指定的维度以0补齐
    for _d in list(set(('member', 'level', 'time', 'dtime', 'lat', 'lon')).difference(set(dims))):
        if temp[_d] is not None:
            xrda = xrda.expand_dims({_d: temp[_d]})
        else:
            xrda = xrda.expand_dims({_d: [0]})

    # 第三步：转置到stda维度
    xrda = xrda.transpose('member', 'level', 'time', 'dtime', 'lat', 'lon')

    # attrs
    stda_attrs = mdgstda.get_stda_attrs(var_name=var_name, **attrs_kwargs)
    # 单位转换
    xrda.values, data_units = mdgstda.numpy_units_to_stda(xrda.values, np_input_units, stda_attrs['var_units'])
    stda_attrs['var_units'] = data_units
    xrda.attrs = stda_attrs

    return xrda


def numpy_to_gridstda(np_input, members, levels, times, dtimes, lats, lons,
                      np_input_units='', var_name='',
                      **attrs_kwargs):
    '''

    [numpy数组转stda网格标准格式]

    Arguments:
        np_input {[ndarray]} -- [numpy数据,维度必须为('member', 'level', 'time', 'dtime', 'lat', 'lon')]
        members {[list or ndarray]} -- [成员列表]
        levels {[list or ndarray]} -- [层次列表]
        times {[list] or ndarray} -- [起报时间列表]
        dtimes {[list or ndarray]} -- [预报失效列表]
        lats {[list or ndarray]} -- [纬度列表]
        lons {[list or ndarray]} -- [经度列表]
        **attrs_kwargs {[type]} -- [其它相关属性，如：data_source='cassandra', level_type='high']

    Keyword Arguments:
        np_input_units {[str]} -- [np_input数据对应的单位，自动转换为能查询到的stda单位]
        var_name {str} -- [要素名] (default: {''})

    Returns:
        [STDA] -- [STDA网格数据]
    '''

    # get attrs
    stda_attrs = mdgstda.get_stda_attrs(var_name=var_name, **attrs_kwargs)

    # 单位转换
    data, data_units = mdgstda.numpy_units_to_stda(np_input, np_input_units, stda_attrs['var_units'])

    stda_attrs['var_units'] = data_units

    members = np.array(members)
    levels = np.array(levels)
    times = np.array(times)
    dtimes = np.array(dtimes)
    lats = np.array(lats)
    lons = np.array(lons)

    '''
    弃用Dataset
    # create STDA xarray.Dataset
    stda_data = xr.Dataset()
    stda_data['data'] = (['member', 'level', 'time', 'dtime', 'lat', 'lon'], data, stda_attrs)

    stda_data.coords['member'] = ('member', members)
    stda_data.coords['level'] = ('level', levels)
    stda_data.coords['time'] = ('time', times)
    stda_data.coords['dtime'] = ('dtime', dtimes)
    stda_data.coords['lat'] = ('lat', lats)
    stda_data.coords['lon'] = ('lon', lons)
    '''

    # create STDA xarray.DataArray
    coords = [('member', members),
              ('level', levels),
              ('time', times),
              ('dtime', dtimes),
              ('lat', lats),
              ('lon', lons), ]
    stda_data = xr.DataArray(data, coords=coords)
    stda_data.attrs = stda_attrs

    return stda_data


def gridstda_full_like(a, fill_value, dtype=None, var_name='', **attrs_kwargs):
    '''

    [返回一个和参数a具有相同维度信息的STDA数据，并且均按fill_value填充该stda]

    Arguments:
        a {[stda]} -- [description]
        fill_value {[scalar]} -- [Value to fill the new object with before returning it]
        **attrs_kwargs {[type]} -- [其它相关属性，如：data_source='cassandra', level_type='high', data_name='ecmwf']

    Keyword Arguments:
        dtype {[dtype, optional]} -- [dtype of the new array. If omitted, it defaults to other.dtype] (default: {None})
        var_name {str} -- [要素名] (default: {''})

    Returns:
        [stda] -- [stda网格数据]
    '''
    stda_data = xr.full_like(a, fill_value, dtype=dtype)
    stda_data.attrs = mdgstda.get_stda_attrs(var_name=var_name, **attrs_kwargs)
    return stda_data


def gridstda_full_like_by_levels(a, levels, dtype=None, var_name='pres', **attrs_kwargs):
    '''

    [返回一个和参数a具有相同维度信息的stda数据，并且按参数levels逐层赋值]

    Arguments:
        a {[type]} -- [description]
        levels {[type]} -- [description]
        **attrs_kwargs {[type]} -- [其它相关属性，如：data_source='cassandra', level_type='high', data_name='ecmwf']

    Keyword Arguments:
        dtype {[dtype, optional]} -- [dtype of the new array. If omitted, it defaults to other.dtype] (default: {None})
        var_name {str} -- [要素名] (default: {'pres'})

    Returns:
        [stda] -- [stda网格数据]
    '''

    # 后续可以改为stda_broadcast_levels， xr.broadcast(a, levels.squeeze())
    stda_data = gridstda_full_like(a, 0, var_name=var_name, **attrs_kwargs)
    for i, lev in enumerate(levels):
        stda_data.values[:, i, :, :, :, :] = lev
    return stda_data


@xr.register_dataarray_accessor('stda')
class __STDADataArrayAccessor(object):
    """
    stda 格式说明: 维度定义为(member, level, time, dtime, lat, lon)
    """

    def __init__(self, xr):
        self._xr = xr

    @property
    def level(self):
        '''
        获取level, 返回值为pd.series
        '''
        return pd.Series(self._xr['level'].values)

    @property
    def fcst_time(self):
        '''
        [获取预报时间（time*dtime)，返回值类型为pd.series]
        '''
        fcst_time = []
        for time in self._xr['time'].values:
            for dtime in self._xr['dtime'].values:
                _ = pd.to_datetime(time).replace(tzinfo=None).to_pydatetime() + datetime.timedelta(hours=int(dtime))
                fcst_time.append(_)
        return pd.Series(fcst_time)

    @property
    def time(self):
        '''
        获取time，返回值类型为pd.series
        '''
        time = pd.to_datetime(self._xr['time'].values)
        return pd.Series(time)

    @property
    def dtime(self):
        '''
        获取dtime，返回值类型为pd.series
        '''
        return pd.Series(self._xr['dtime'].values)

    @property
    def lat(self):
        '''
        获取lat，返回值类型为pd.series
        '''
        return pd.Series(self._xr['lat'].values)

    @property
    def lon(self):
        '''
        获取lon，返回值类型为pd.series
        '''
        return pd.Series(self._xr['lon'].values)

    @property
    def member(self):
        '''
        获取member，返回值类型为pd.series
        '''
        return pd.Series(self._xr['member'].values)

    def description(self):
        '''
        获取描述信息，格式如下:
        起报时间: Y年m月d日H时
        预报时间: Y年m月d日H时
        预报时效: 小时
        '''
        init_time = self.time[0]
        fhour = self.dtime[0]
        fcst_time = self.fcst_time[0]

        if fhour != 0:
            description = '起报时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n预报时间: {1:%Y}年{1:%m}月{1:%d}日{1:%H}时\n预报时效: {2}小时'.format(
                init_time, fcst_time, fhour)
        else:
            description = '分析时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n实况/分析'.format(init_time)
        return description

    def description_point(self, describe=''):
        '''
        获取描述信息，格式如下
        起报时间: Y年m月d日H时
        [data_name]N小时预报describe
        预报点: lon, lat

        起报时间: Y年m月d日H时
        [data_name]实况info
        分析点: lon, lat
        '''
        init_time = self.time[0]
        fhour = self.dtime[0]
        point_lon = self.lon[0]
        point_lat = self.lat[0]
        data_name = self.member[0].upper()

        if(fhour != 0):
            description = '起报时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n[{1}]{2}小时预报{5}\n预报点: {3}, {4}'.format(
                init_time, data_name, fhour, point_lon, point_lat, describe)
        else:
            description = '分析时间: {0:%Y}年{0:%m}月{0:%d}日{0:%H}时\n[{1}]实况/分析{4}\n分析点: {2}, {3}'.format(
                init_time, data_name, point_lon, point_lat, describe)
        return description

    def get_dim_value(self, dim_name):
        '''
        获取维度信息，如果dim_name=='fcst_time'情况下，特殊处理，范围time*dtime
        返回值为numpy
        '''
        if dim_name == 'fcst_time':
            return self.fcst_time.values
        if dim_name == 'time':
            return self.time.values
        return self._xr[dim_name].values

    def get_value(self, ydim='lat', xdim='lon', xunits=False):
        '''
        获取二维数据，假如stda不是二维的数据，则报错
        返回值为numpy
        '''
        if xdim == 'fcst_time':
            if self._xr['time'].values.size == 1:  # 因为是二维，假如time维长度为1，则有维度的肯定在dtime维
                xdim = 'dtime'
            else:
                xdim = 'time'
        if ydim == 'fcst_time':
            if self._xr['time'].values.size == 1:
                ydim = 'dtime'
            else:
                ydim = 'time'
        data = self._xr.squeeze().transpose(ydim, xdim).values
        if xunits == True:
            data = data * units(self._xr.attrs['var_units'])
        return data


if __name__ == '__main__':
    pass
