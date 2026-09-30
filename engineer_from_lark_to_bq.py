import json

import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

# https://open.larksuite.com/api-explorer/cli_a9474cd9e8f8de15?apiName=list&from=op_doc&project=bitable&resource=app.table.record&version=v1

# SDK 使用说明: https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/server-side-sdk/python--sdk/preparations-before-development
# 以下示例代码默认根据文档示例值填充，如果存在代码问题，请在 API 调试台填上相关必要参数后再复制代码使用
# 复制该 Demo 后, 需要将 "YOUR_APP_ID", "YOUR_APP_SECRET" 替换为自己应用的 APP_ID, APP_SECRET.
def main():
    # 创建client
    client = lark.Client.builder() \
        .app_id("YOUR_APP_ID") \
        .app_secret("YOUR_APP_SECRET") \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: ListAppTableRecordRequest = ListAppTableRecordRequest.builder() \
        .app_token("bascnd0HM3KAyiZJELxfMHRrGZc") \
        .table_id("tblEGB3HKvDrpj71") \
        .view_id("vewp7nmiS4") \
        .filter("AND(CurrentValue.[Height]>180, CurrentValue.[Weight]>150)") \
        .sort("["fieldName1 DESC","fieldName2 ASC"]") \
        .field_names("["fieldName1"]") \
        .text_field_as_array(true) \
        .user_id_type("open_id") \
        .display_formula_ref(true) \
        .automatic_fields(true) \
        .page_token("recP750ZNJ") \
        .page_size(10) \
        .build()

    # 发起请求
    response: ListAppTableRecordResponse = client.bitable.v1.app_table_record.list(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    main()