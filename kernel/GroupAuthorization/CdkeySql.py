import time
from utils.sqliteutil.basesql import BaseSql
from dataclasses import dataclass
from enum import Enum
import datetime

class CdkeyState(Enum):
    UNUSED = 0
    USED = 1

@dataclass
class CdkeyTable:
    cdkey: str = None           # CDKEY
    createtime: int = None      # 创建时间，为时间戳
    validatetime: int = None    # 有效期，为时间戳
    value: int = None           # 面额，单位为天
    state: str = None           # 状态，表示已使用或者未使用


class CdkeySql(BaseSql):
    def __init__(self, DataBaseName=None):
        super().__init__(DataBaseName)
        self.CreateTable()

    def CreateTable(self):
        sql = '''
        CREATE TABLE IF NOT EXISTS cdkeys (
            CDKEY TEXT PRIMARY KEY,
            CREATETIME TEXT,
            VALIDATETIME TEXT,
            VALUE INTEGER,
            STATE TEXT
        )
        '''
        self.ExecuteSingleSql(sql)

    def InsertTable(self, data: CdkeyTable):
        if not data.cdkey or not data.validatetime or not data.value:
            raise TypeError("All parameters must be provided.")

        createtime = datetime.datetime.fromtimestamp(data.createtime).strftime('%Y-%m-%d %H:%M:%S')
        validatetime = datetime.datetime.fromtimestamp(data.validatetime).strftime('%Y-%m-%d %H:%M:%S')

        sql = '''
        INSERT INTO cdkeys (CDKEY, CREATETIME, VALIDATETIME, VALUE, STATE)
        VALUES (?, ?, ?, ?, ?)
        '''
        self.ExecuteSingleSql(sql, (data.cdkey, createtime, validatetime, data.value, 'UNUSED'))     # 刚插入的时候使用状态肯定是未使用

    def SelectCdkey(self, used: bool = None):
        if used is not None and not isinstance(used, bool):
            raise TypeError("Invalid input. 'used' must be a boolean.")

        sql = '''
        SELECT * FROM cdkeys
        '''
        if used is not None:
            sql += ' WHERE STATE = "USED"' if used else ' WHERE STATE = "UNUSED"'

        results = self.ExecuteSingleSql(sql)[1]

        if len(results) == 0:
            return None

        cdkey_list = []
        for result in results:
            cdkey_obj = CdkeyTable()
            cdkey_obj.cdkey = result[0]
            cdkey_obj.createtime = datetime.datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S').timestamp()
            cdkey_obj.validatetime = datetime.datetime.strptime(result[2], '%Y-%m-%d %H:%M:%S').timestamp()
            cdkey_obj.value = result[3]
            cdkey_obj.state = CdkeyState[result[4]].value
            cdkey_list.append(cdkey_obj)

        return cdkey_list

    def SelectCdkeyByCdkey(self, cdkey):

        sql = '''
        SELECT * FROM cdkeys WHERE CDKEY = '
        '''.strip()
        sql += cdkey
        sql += '\''

        result = self.ExecuteSingleSql(sql)[1]

        if len(result) == 0:
            return None

        result = result[0]
        cdkey_obj = CdkeyTable()
        cdkey_obj.cdkey = result[0]
        cdkey_obj.createtime = datetime.datetime.strptime(result[1], '%Y-%m-%d %H:%M:%S').timestamp()
        cdkey_obj.validatetime = datetime.datetime.strptime(result[2], '%Y-%m-%d %H:%M:%S').timestamp()
        cdkey_obj.value = result[3]
        cdkey_obj.state = CdkeyState[result[4]].value

        return cdkey_obj

    def UpdateCdkeyState(self, cdkey: str, state: CdkeyState):
        if not all([cdkey, state]):
            raise TypeError("'cdkey' and 'state' must be provided.")

        sql = '''
        UPDATE cdkeys SET STATE = ? WHERE CDKEY = ?
        '''
        self.ExecuteSingleSql(sql, (CdkeyState(state).name, cdkey))

    def DeleteCdkeyByCdkey(self, cdkey: str):
        if not cdkey:
            raise TypeError("'cdkey' must be provided.")

        sql = '''
        DELETE FROM cdkeys WHERE CDKEY = ?
        '''
        self.ExecuteSingleSql(sql, (cdkey,))


# if __name__ == '__main__':
#     # 创建一个 CdkeyTable 实例
#     cdkey_table = CdkeySql()
#
#     # 插入一些 cdkey 数据
#     cdkey1 = CdkeyTable("CDKEY1", time.time(), time.time()+1200, 50, CdkeyState.UNUSED)
#     cdkey_table.InsertTable(cdkey1)
#
#     cdkey2 = CdkeyTable("CDKEY2", time.time(), time.time()+1200, 100, CdkeyState.UNUSED)
#     cdkey_table.InsertTable(cdkey2)
#
#     # 查询所有未使用的 cdkey
#     unused_cdkeys = cdkey_table.SelectCdkeyByCdkey(used=False)
#     print("未使用的cdkey:")
#     if unused_cdkeys is not None:
#         for cdkey_obj in unused_cdkeys:
#             print(cdkey_obj)
#
#     # 查询所有已使用的 cdkey
#     used_cdkeys = cdkey_table.SelectCdkeyByCdkey(used=True)
#     print("\n已使用的cdkey:")
#     if used_cdkeys is not None:
#         for cdkey_obj in used_cdkeys:
#             print(cdkey_obj)
#
#     # 更新某个 cdkey 的状态为已使用
#     cdkey_table.UpdateCdkeyState("CDKEY1", CdkeyState.USED)
#
#     # 再次查询所有未使用的 cdkey
#     unused_cdkeys = cdkey_table.SelectCdkeyByCdkey(used=False)
#     print("\n更新后的未使用的cdkey:")
#     for cdkey_obj in unused_cdkeys:
#         print(cdkey_obj)
#
#     # 删除一个 cdkey
#     cdkey_table.DeleteCdkeyByCdkey("CDKEY2")
#
#     # 再次查询所有 cdkey
#     all_cdkeys = cdkey_table.SelectCdkeyByCdkey()
#     print("\n剩余的cdkey:")
#     for cdkey_obj in all_cdkeys:
#         print(cdkey_obj)
