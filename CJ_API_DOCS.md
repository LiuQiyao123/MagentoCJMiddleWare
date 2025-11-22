# CJ Dropshipping API Documentation

> Auto-generated from official documentation

#  1 鉴权
 ##  1 鉴权
 ###  1.1 获取 Token - 独立用户（POST）
 API 的安全机制，获取accessToken。accessToken 过期时间为15天，refreshToken过期时间为180天。若accessToken过期，
可用refreshToken重新刷新accessToken，若refreshToken过期，需要重新获取accessToken。 > 每5分钟只能调用1次

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "apiKey": "CJUserNum@api@xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| apiKey | CJ API Key | string | 是 | 200 | [获取 API Key  (opens new window)](https://www.cjdropshipping.com/myCJ.html#/apikey) |
 > 如何获取API Key:

 跳转到[获取API Key  (opens new window)](https://www.cjdropshipping.com/myCJ.html#/apikey), 点击按钮"Generate"

 

 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "openId": 123456789,
        "accessToken": "c50f01a5d910400fb401944569fe0b0c",
        "accessTokenExpiryDate": "2021-07-12T20:08:13+08:00",
        "refreshToken": "16bb512baf74491ba25ea65b8b2dd597",
        "refreshTokenExpiryDate": "2021-08-04T20:08:13+08:00",
        "createDate": "2021-07-05T20:08:13+08:00"
    },
    "requestId": "31c7760c-068e-41c7-aeed-5f2a7f598f22"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| openId | CJ提供的开发者id | Long | 20 |  |
| accessToken | Access Token | string | 200 |  |
| accessTokenExpiryDate | Access Token 过期时间 | string | 200 |  |
| refreshToken | Refresh Token | string | 200 |  |
| refreshTokenExpiryDate | Refresh Token 过期时间 | string | 200 |  |
| createDate | 创建时间 | string | 200 |  |
 error

 ```
{
    "code": 1601000,
    "result": false,
    "message": "User not find",
    "data": null,
    "requestId": "a18c9793-7c99-42f9-970b-790eecdceba2"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.2 刷新accessToken（POST）
 通过refreshToken刷新accessToken的过期时间。accessToken过期时间为15天。

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/authentication/refreshAccessToken

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/authentication/refreshAccessToken' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "refreshToken": "3d3b01404da04be8b6795d7e9823cee5"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| refreshToken | 刷新 Token | string | 是 | 80 |  |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "accessToken": "c50f01a5d910400fb401944569fe0b0c",
        "accessTokenExpiryDate": "2021-07-06T04:08:13+08:00",
        "refreshToken": "16bb512baf74491ba25ea65b8b2dd597",
        "refreshTokenExpiryDate": "2021-08-04T20:08:13+08:00",
        "createDate": "2021-07-05T20:08:13+08:00"
    },
    "requestId": "31c7760c-068e-41c7-aeed-5f2a7f598f22"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| accessToken | Access Token | string | 200 |  |
| accessTokenExpiryDate | Access Token 过期时间 | string | 200 |  |
| refreshToken | Refresh Token | string | 200 |  |
| refreshTokenExpiryDate | Refresh Token 过期时间 | string | 200 |  |
| createDate | 创建时间 | string | 200 |  |
 error

 ```
{
    "code": 1600003,
    "result": false,
    "message": "Refresh token is failure",
    "data": null,
    "requestId": "0b20dc1a-0043-43a7-a7c0-51ca6c61d976"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.3 登出（POST）
 API 的安全机制，登出后，accessToken 和 refreshToken 都会失效。

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/authentication/logout

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/authentication/logout' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": true,
    "requestId": "b1d3728d-8a29-417e-9983-6df9926aaa49"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
    "code": 1600001,
    "result": false,
    "message": "Authentication failed",
    "data": null,
    "requestId": "5aa2bb6e-42fa-4e0a-ae88-1833c2c1c883"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ##  1.4 附属商家授权
 ###  1.4.1 附属商家获取授权地址（POST）
 返回CJ页面跳转URL(登陆页或者注册页)，并返回授权密钥。

 > 前提：1.需要传入独立商家的accessToken; 2.涉及的独立商家需要设置接收授权code的接口(看1.4.2)

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/authentication/getAuthorizeUrl

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/authentication/getAuthorizeUrl' \
                --header 'Content-Type: application/json' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxx' \
                --data-raw '{
                   "email": "v0pjsw5t@linshiyouxiang.net",
                   "redirectUri":"https://yourapp.com/xxx",
                   "callbackUri":"https://yourapp.com/xxx",
                   "userName":"your userName",
                   "state":"xxxxxx"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| email | 邮箱 | string | 是 | 100 |  |
| redirectUri | 授权之后需要跳转的合作方地址 | String | 否 | 200 | 授权完成之后需要跳转到合作方页面地址 |
| callbackUri | 授权之后通知code接口地址 | String | 否 | 200 | 授权之后通知code接口地址 |
| userName | 用户名称 | string | 是 | 40 | 用于CJ展示 |
| state | 透传参数 | string | 否 | 40 | 通知code时,会原样返回 |
| openId | Long | Long | 否 | 40 | 授权成功获取access_Token时返回的 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
    "code": 200,
    "result": true,
    "message": "Success",
    "data":"https://cjdropshipping.com/apiAuthorization.html?secretKey=XNbDqGDoCMkNirc77EBhxCeu4NPwD4mZ&type=autoCreate",
    "requestId": "31c7760c-068e-41c7-aeed-5f2a7f598f22"
},
    "requestId": "31c7760c-068e-41c7-aeed-5f2a7f598f22"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| cjRedirectUri | cj授权跳转地址 | string | 200 |  |
 error

 ```
{
    "code": 1601000,
    "result": false,
    "message": "accessToken not validate",
    "data": null,
    "requestId": "a18c9793-7c99-42f9-970b-790eecdceba2"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.4.2 合作方接收授权成功code接口(合作方提供)
 用户在cj登录之后，CJ会生成授权code,并推送到合作方，需要合作方提供接收授权code的接口。

 > 要求: 请求方法： POST

 ####  接口入参
 | 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| code | 授权成功后CJ返回的参数 | string | 是 | 100 |  |
| state | 透传参数 | string | 否 |  | 1.4.1传过来的值, 原值返回 |
 ####  接口出参
 | 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| result | 处理结果 | string | 是 |  | 0=成功, 其他=失败 |
| message | 处理结果消息 | string | 是 |  | 具体消息内容 |
 ###  1.4.3 附属商pe通过code交换accessToken (POST)
 通过授权code交换accessToken.

 > accessToken 过期时间为15天，refreshToken 过期时间为180天。若accessToken 过期，可用refreshToken重新刷新accessToken的失效时间，若refreshToken过期，需要重新授权。

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/authentication/exchangeAccessToken

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/authentication/exchangeAccessToken' \
                --header 'Content-Type: application/json' \
                --header 'CJ-Access-Token: xxxxxxxx' \
                --data-raw '{
                    "code": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| code | 授权code | string | 是 | 100 |  |
 ```

#### 返回
success

```
{
"code": 200,
"result": true,
"message": "Success",
"data": {
"openId": 123456789,
"accessToken": "c50f01a5d910400fb401944569fe0b0c",
"accessTokenExpiryDate": "2022-12-08T20:08:13+08:00",
"refreshToken": "16bb512baf74491ba25ea65b8b2dd597",
"refreshTokenExpiryDate": "2023-06-08T20:08:13+08:00",
"createDate": "2022-012-08T20:08:13+08:00"
},
"requestId": "31c7760c-068e-41c7-aeed-5f2a7f598f22"
} ```
| 返回字段                 | 字段意思               | 字段类型   | 长度  | 备注 |
|------------------------|--------------------|--------|-----| --- |
| openId                 | CJ提供的开发者id     | Long   | 20  |  |
| accessToken            | Access Token       | string | 200 |  |
| accessTokenExpiryDate  | Access Token 过期时间  | string | 200 |  |
| refreshToken           | Refresh Token      | string | 200 |  |
| refreshTokenExpiryDate | Refresh Token 过期时间 | string | 200 |  |
| createDate             | 创建时间               | string | 200 |  |

error

```
{
"code": 1601000,
"result": false,
"message": "code not found",
"data": null,
"requestId": "a18c9793-7c99-42f9-970b-790eecdceba2"
} ```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](../../api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |

```


---

#  5 交易
 ##  1 订单
 ###  1.1 创建订单 V2（POST）
 - 创建订单,
 - 如果要使用余额支付，payType传2, 会将创建成功的订单进行后续操作：添加购物车、确认订单、余额支付,
 - 如果不要使用余额支付，payType传3
 - header中新增platformToken参数, 获取platformToken的方式与CJ Access Token的方式相同, 如果不是被要求，该值可以为空. (2025-01-08 更新)

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/createOrderV2

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/createOrderV2' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'platformToken: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "orderNumber": "1234",
                    "shippingZip": "123",
                    "shippingCountry": "123",
                    "shippingCountryCode": "US",
                    "shippingProvince": "123",
                    "shippingCity": "132",
                    "shippingCounty": "",
                    "shippingPhone": "111",
                    "shippingCustomerName": "123213",
                    "shippingAddress": "123213",
                    "shippingAddress2": "123213",
                    "taxId": "123",
                    "remark": "note",
                    "email": "",
                    "consigneeID": "",
                    "payType": "",
                    "shopAmount": "",
                    "logisticName": "PostNL",
                    "fromCountryCode": "CN",
                    "houseNumber": "123",
                    "platform": "shopify",
                    "iossType": "",
                    "iossNumber": "",
                    "products": [
                        {
                            "vid": "92511400-C758-4474-93CA-66D442F5F787",
                            "quantity": 1,
                            "storeLineItemId": "test-lineItemId-1111"
                        }
                    ]
                }'

```
| Parameter | Definition | Type | Required | Length | Note |
| --- | --- | --- | --- | --- | --- |
| orderNumber | 订单编号 | string | 是 | 50 |  |
| shippingZip | 目的地邮编 | string | 否 | 20 |  |
| shippingCountryCode | 目的地国家简码 | string | 是 | 20 | 参照:[国家信息](/zh/api/api2/standard/ps-country.html), 请使用二字码 |
| shippingCountry | 目的地国家 | string | 是 | 50 |  |
| shippingProvince | 目的地省 | string | 是 | 50 |  |
| shippingCity | 目的地城市 | string | 是 | 50 |  |
| shippingCounty | 目的地县 | String | 否 | 50 |  |
| shippingPhone | 收货人电话 | string | 否 | 20 |  |
| shippingCustomerName | 收货人名称 | string | 是 | 50 |  |
| shippingAddress | 收货人地址 | string | 是 | 200 |  |
| shippingAddress2 | 收货人地址2 | string | 否 | 200 |  |
| houseNumber | 门牌号 | String | 否 | 20 |  |
| email | 邮箱 | String | 否 | 50 |  |
| taxId | 税号 | string | 否 | 20 |  |
| remark | 订单备注 | string | 否 | 500 |  |
| consigneeID | 收货人id | string | 否 | 20 |  |
| payType | payType=2 (余额支付),payType=3 (不使用余额支付), | int | 否 | 10 | 如果使用余额支付payType必须是2 |
| shopAmount | 订单金额 | BigDecimal | 否 | 20 |  |
| logisticName | 物流名称 | string | 是 | 50 |  |
| fromCountryCode | 发货国家 | string | 是 | 20 | 参照:[国家信息](/zh/api/api2/standard/ps-country.html), 请使用二字码 |
| platform | 平台类型（比如：shopify） | String | 否 | 20 | 如果需要开通指定的平台，需要找业务员申请开通，否则就使用默认的平台类型 |
| iossType | ioss类型 | int | 否 | 20 | IOSS类型，选项：1=无IOSS（在没有IOSS的情况下申报订单时，收款人将被要求支付增值税和其他相关费用。），2=用我自己的IOSS申报（请确保提供的IOSS是有效的，并与欧盟的目的地国家相关联。如果目的地国家没有与正确的IOSS相关联，申报将在没有IOSS的情况下进行。），3=用CJ的IOSS进行申报（建议申报您的商店订单金额。如果您选择用CJ订单金额申报，您将对相关风险负责。CJ的IOSS不适用于价值超过150欧元的订单，收款人需要支付增值税。), [设置界面  (opens new window)](https://www.cjdropshipping.com/my.html#/profile/declaration) |
| iossNumber | ioss编号 | String | 否 | 10 | 如果iosType=3，则该值固定为CJ-IOSS |
| products |  | list | 是 | 20 |  |
| - vid | CJ 变体 id | string | 否 | 50 | vid与sku不能都为空，如果vid为空，则使用sku查询CJ变体，如果都提供，会校验两者必须是相同的变体，不相同则校验失败。如果客户维度开通了可以传非CJsku权限，则vid为必传项 |
| - sku | CJ 变体 sku | string | 否 | 50 | vid与sku不能都为空，如果sku为空，则使用vid查询CJ变体，如果都提供，会校验两者必须是相同的变体，不相同则校验失败 |
| - quantity | 变体 数量 | int | 是 | 10 |  |
| - unitPrice | 商品单价 | BigDecimal | 否 | 20 | unit: $ (USD) |
| - storeLineItemId | 店铺订单的lineItemId | String | 否 | 125 |  |
| - podProperties | POD定制信息 | String | 否 | 500 | podProperties是一个字符串，1：Pod2.0 示例:[{"areaName":"LogoArea","links":["2：Pod3.0 示例:{"links": ["生产图URL (支持多张)"],"effectImgs": ["效果图URL (只支持一张)"]} |
 platform

 | 取值 |
| --- |
| shopify |
| Lazada |
| woocommerce |
| tiktok |
| aliexpress |
| tiktok_us |
| Temu |
| ebay |
| shopee |
| shoplazza |
| mercado |
| allvalue |
| nuvemshop |
| square |
| bigcommerce |
| squarespace |
| magento |
| prestashop |
| etsy |
| wix |
 ####  Return
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "orderNumber": "",
        "orderId": "123434',
        "shipmentOrderId": "",
        "iossAmount": "",
        "iossTaxHandlingFee": "",
        "iossAmount": "",
        "postageAmount": "",
        "productAmount": "",
        "productOriginalAmount": "",
        "productDiscountAmount": "",
        "postageDiscountAmount": "",
        "postageOriginalAmount": "",
        "totalDiscountAmount": "",
        "actualPayment": "",
        "orderOriginalAmount": "",
        "cjPayUrl": "",
        "orderAmount": "",
        "logisticsMiss": "",
        "productInfoList": [
            {
                "storeLineItemId": "test-lineItemId-1111",
                "lineItemId": "",
                "variantId": "",
                "isGroup": true,
                "quantity": 10,
                "subOrderProducts": [
                    {
                        "lineItemId": "",
                        "variantId": "",
                        "quantity": ""
                    }
                ]
            }
        ],
        "orderStatus": "",
        "interceptOrderReasons": [
            {
                "code": 1001,
                "message": ""
            }
        ]
    },
    "requestId": "9eddf3f5-bd3d-4fae-a4f2-028cbb90db97"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 data information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| orderId | CJ 订单号 | string | 200 | 如果传入的商品vid非CJ的SKU，因为订单号会变化，则不会返回CJ订单号。您可以监听webhook获取到最新的CJ订单号 |
| orderNumber | 客户订单号 | string | 200 |  |
| shipmentOrderId | 母订单号Id | string | 200 |  |
| iossAmount | ioss金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| iossTaxHandlingFee | ioss税费 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageAmount | 物流费用 | BigDecimal | （18，2） | Unit: $ (USD） |
| productAmount | 商品金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| productOriginalAmount | 商品总金额(折前) | BigDecimal | （18，2） | Unit: $ (USD） |
| productDiscountAmount | 商品优惠金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageDiscountAmount | 运费折扣金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageOriginalAmount | 运费折扣前金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| totalDiscountAmount | 订单优惠后的总金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| actualPayment | 实付金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| orderOriginalAmount | 订单原总金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| cjPayUrl | CJ支付页跳转地址 | string | 200 |  |
| orderAmount | 订单金额 | BigDecimal | 200 |  |
| logisticsMiss | 物流缺失标识 | Boolean | 10 |  |
| orderStatus | 订单中心订单状态 | string | 10 |  |
| productInfoList | 订单商品信息 | list |  |  |
| interceptOrderReasons | 订单拦截信息 | list |  |  |
 product information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| storeLineItemId | 店铺订单的lineItemId | String | 否 | 125 |
| lineItemId | CJ订单item的唯一id | string | 50 |  |
| variantId | 变体 id | string | 50 |  |
| quantity | 数量 | int | 20 |  |
| isGroup | 是否组合主商品 | boolean | 10 |  |
| subOrderProducts | 组合子商品 | list | 10 |  |
| - lineItemId | CJ订单item的唯一id | string | 50 |  |
| - variantId | 变体 id | string | 50 |  |
| - quantity | 数量 | int | 20 |  |
 Order interception information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | code | int | 50 |  |
| message | 拦截信息 | string | 200 |  |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | error code | int | 20 | [Reference error code](/zh/api/api2/standard/ps-code.html) |
| result | Whether or not the return is normal | boolean | 1 |  |
| message | return message | string | 200 |  |
| data | return data | object |  | interface data return |
| requestId | requestId | string | 48 | Flag request for logging errors |
 ###  1.2 创建订单 V3（POST）
 - 创建订单
 - header中新增platformToken参数, 获取platformToken的方式与CJ Access Token的方式相同, 如果不是被要求，该值可以为空. (2025-01-08 更新)

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/createOrderV3

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/createOrderV3' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'platformToken: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "orderNumber": "1234",
                    "shippingZip": "123",
                    "shippingCountry": "123",
                    "shippingCountryCode": "US",
                    "shippingProvince": "123",
                    "shippingCity": "132",
                    "shippingCounty": "",
                    "shippingPhone": "111",
                    "shippingCustomerName": "123213",
                    "shippingAddress": "123213",
                    "shippingAddress2": "123213",
                    "taxId": "123",
                    "remark": "note",
                    "email": "",
                    "consigneeID": "", 
                    "shopAmount": "",
                    "logisticName": "PostNL",
                    "fromCountryCode": "CN",
                    "houseNumber": "123",
                    "platform": "shopify",
                    "iossType": "",
                    "iossNumber": "",
                    "products": [
                        {
                            "vid": "92511400-C758-4474-93CA-66D442F5F787",
                            "quantity": 1,
                            "storeLineItemId": "test-lineItemId-1111"
                        }
                    ]
                }'

```
| Parameter | Definition | Type | Required | Length | Note |
| --- | --- | --- | --- | --- | --- |
| orderNumber | 订单编号 | string | 是 | 50 |  |
| shippingZip | 目的地邮编 | string | 否 | 20 |  |
| shippingCountryCode | 目的地国家简码 | string | 是 | 20 | 参照:[国家信息](/zh/api/api2/standard/ps-country.html), 请使用二字码 |
| shippingCountry | 目的地国家 | string | 是 | 50 |  |
| shippingProvince | 目的地省 | string | 是 | 50 |  |
| shippingCity | 目的地城市 | string | 是 | 50 |  |
| shippingCounty | 目的地县 | String | 否 | 50 |  |
| shippingPhone | 收货人电话 | string | 否 | 20 |  |
| shippingCustomerName | 收货人名称 | string | 是 | 50 |  |
| shippingAddress | 收货人地址 | string | 是 | 200 |  |
| shippingAddress2 | 收货人地址2 | string | 否 | 200 |  |
| houseNumber | 门牌号 | String | 否 | 20 |  |
| email | 邮箱 | String | 否 | 50 |  |
| taxId | 税号 | string | 否 | 20 |  |
| remark | 订单备注 | string | 否 | 500 |  |
| consigneeID | 收货人id | string | 否 | 20 |  |
| shopAmount | 订单金额 | BigDecimal | 否 | 20 |  |
| logisticName | 物流名称 | string | 是 | 50 |  |
| fromCountryCode | 发货国家 | string | 是 | 20 | 参照:[国家信息](/zh/api/api2/standard/ps-country.html), 请使用二字码 |
| platform | 平台类型（比如：shopify） | String | 否 | 20 | 如果需要开通指定的平台，需要找业务员申请开通，否则就使用默认的平台类型 |
| iossType | ioss类型 | int | 否 | 20 | IOSS类型，选项：1=无IOSS（在没有IOSS的情况下申报订单时，收款人将被要求支付增值税和其他相关费用。），2=用我自己的IOSS申报（请确保提供的IOSS是有效的，并与欧盟的目的地国家相关联。如果目的地国家没有与正确的IOSS相关联，申报将在没有IOSS的情况下进行。），3=用CJ的IOSS进行申报（建议申报您的商店订单金额。如果您选择用CJ订单金额申报，您将对相关风险负责。CJ的IOSS不适用于价值超过150欧元的订单，收款人需要支付增值税。), [设置界面  (opens new window)](https://www.cjdropshipping.com/my.html#/profile/declaration) |
| iossNumber | ioss编号 | String | 否 | 10 | 如果iosType=3，则该值固定为CJ-IOSS |
| products |  | list | 是 | 20 |  |
| - vid | CJ 变体 id | string | 否 | 50 | vid与sku不能都为空，如果vid为空，则使用sku查询CJ变体，如果都提供，会校验两者必须是相同的变体，不相同则校验失败。如果客户维度开通了可以传非CJsku权限，则vid为必传项。 |
| - sku | CJ 变体 sku | string | 否 | 50 | vid与sku不能都为空，如果sku为空，则使用vid查询CJ变体，如果都提供，会校验两者必须是相同的变体，不相同则校验失败 |
| - quantity | 变体 数量 | int | 是 | 50 |  |
| - storeLineItemId | 店铺订单的lineItemId | String | 否 | 125 |  |
| - unitPrice | 商品单价 | BigDecimal | 否 | 50 |  |
| - podProperties | POD定制信息 | String | 否 | 500 | podProperties是一个字符串，1：Pod2.0 示例:[{"areaName":"LogoArea","links":["2：Pod3.0 示例:{"links": ["生产图URL (支持多张)"],"effectImgs": ["效果图URL (只支持一张)"]} |
 platform

 | 取值 |
| --- |
| shopify |
| Lazada |
| woocommerce |
| tiktok |
| aliexpress |
| tiktok_us |
| Temu |
| ebay |
| shopee |
| shoplazza |
| mercado |
| allvalue |
| nuvemshop |
| square |
| bigcommerce |
| squarespace |
| magento |
| prestashop |
| etsy |
| wix |
 ####  Return
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "orderNumber": "",
        "orderId": "123434',
        "shipmentOrderId": "",
        "iossAmount": ,
        "iossTaxHandlingFee": ,
        "iossAmount": ,
        "postageAmount": ,
        "productAmount": "",
        "productOriginalAmount": "",
        "productDiscountAmount": "",
        "postageDiscountAmount": "",
        "postageOriginalAmount": "",
        "totalDiscountAmount": "",
        "actualPayment": "",
        "orderOriginalAmount": "",
        "cjPayUrl": "",
        "orderAmount": "",
        "logisticsMiss": "",
        "productInfoList": [
            {
                "storeLineItemId": "test-lineItemId-1111",
                "lineItemId": "",
                "variantId": "",
                "isGroup": true,
                "quantity": 10,
                "subOrderProducts": [
                    {
                        "lineItemId": "",
                        "variantId": "",
                        "quantity": ""
                    }
                ]
            }
        ],
        "orderStatus": "",
        "interceptOrderReasons": [
            {
                "code": 1001,
                "message": ""
            }
        ]
    },
    "requestId": "9eddf3f5-bd3d-4fae-a4f2-028cbb90db97"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 data information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| orderId | CJ 订单号 | string | 200 | 如果传入的商品vid非CJ的SKU，因为订单号会变化，则不会返回CJ订单号。您可以监听webhook获取到最新的CJ订单号 |
| orderNumber | 客户订单号 | string | 200 |  |
| shipmentOrderId | 母订单号Id | string | 200 |  |
| iossAmount | ioss金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| iossTaxHandlingFee | ioss税费 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageAmount | 物流费用 | BigDecimal | （18，2） | Unit: $ (USD） |
| productAmount | 商品金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| productOriginalAmount | 商品总金额(折前) | BigDecimal | （18，2） | Unit: $ (USD） |
| productDiscountAmount | 商品优惠金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageDiscountAmount | 运费折扣金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| postageOriginalAmount | 运费折扣前金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| totalDiscountAmount | 订单优惠后的总金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| actualPayment | 实付金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| orderOriginalAmount | 订单原总金额 | BigDecimal | （18，2） | Unit: $ (USD） |
| cjPayUrl | CJ支付页跳转地址 | string | 200 |  |
| orderAmount | 订单金额 | BigDecimal | 200 |  |
| logisticsMiss | 物流缺失标识 | Boolean | 10 |  |
| orderStatus | 订单中心订单状态 | string | 10 |  |
| productInfoList | 订单商品信息 | list |  |  |
| interceptOrderReasons | 订单拦截信息 | list |  |  |
 product information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| storeLineItemId | 店铺订单的lineItemId | String | 否 | 125 |
| lineItemId | CJ订单item的唯一id | string | 50 |  |
| variantId | 变体 id | string | 50 |  |
| quantity | 数量 | int | 20 |  |
| isGroup | 是否组合主商品 | boolean | 10 |  |
| subOrderProducts | 组合子商品 | list | 10 |  |
| - lineItemId | CJ订单item的唯一id | string | 50 |  |
| - variantId | 变体 id | string | 50 |  |
| - quantity | 数量 | int | 20 |  |
 Order interception information

 | Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | code | int | 50 |  |
| message | 拦截信息 | string | 200 |  |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | error code | int | 20 | [Reference error code](/zh/api/api2/standard/ps-code.html) |
| result | Whether or not the return is normal | boolean | 1 |  |
| message | return message | string | 200 |  |
| data | return data | object |  | interface data return |
| requestId | requestId | string | 48 | Flag request for logging errors |
 ###  1.3 加入购物车（POST）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/addCart

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/addCart' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "cjOrderIdList": ["SD25080109282603297001"]
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| cjOrderIdList | CJ 订单 id列表 | list | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 200,
    "message": "Congratulation! Well done!",
    "data": {
        "successCount": 1,
        "addSuccessOrders": [
            "SD25080109282603297001"
        ],
        "unInterceptAddressCount": 0,
        "interceptOrders": []
    }
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回(订单号) |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.4 购物车确认（POST）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/addCartConfirm

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/addCartConfirm' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "cjOrderIdList": ["SD25080109282603297001"]
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| cjOrderIdList | 订单 id | list | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 200,
    "message": "Congratulation! Well done!",
    "data": {
        "successCount": 1,
        "submitSuccess": true,
        "shipmentsId": "",
        "result": 0,
        "interceptOrders": []
    }
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| - successCount | 成功数量 |  |  |  |
| - submitSuccess | 是否提交成功 |  |  |  |
| - shipmentsId | Shipment Order Id |  |  | 请记录好 |
| - result |  |  |  |  |
| - interceptOrders |  | List |  | 被拦截的订单id列表 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.5 保存提交母单（POST）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/saveGenerateParentOrder

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/saveGenerateParentOrder' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "shipmentOrderId": "SD25080109282603297001"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| shipmentOrderId | Shipment Order Id | string | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
  "success": true,
  "message": "",
  "data": {
    "orderMoney": 99.99,
    "payExpireTime": "2024-12-31 23:59:59",
    "payId": "PAY123456789",
    "result": 0,
    "submitSuccess": true,
    "unMatchOrderCodes": ["ORDER001", "ORDER002"],
    "successOrders": ["ORDER003", "ORDER004"],
    "unMatchProductCodes": ["PROD001", "PROD002"],
    "paymentInformation": {
      "actualPayment": 89.99,
      "balanceDeduction": 10.00,
      "billAmount": 12.50,
      "canDeduct": true,
      "commodityDiscount": 5.00,
      "commodityTotalAmount": 94.99,
      "couponAmount": 15.00,
      "freight": 5.00,
      "iossAmount": 2.50,
      "iossNumber": "IOSS123456",
      "iossTaxHandlingFee": 0.50,
      "iossTaxes": 2.00,
      "iossType": 3,
      "orderOriginalAmount": 104.99,
      "orderProductAmount": 94.99,
      "payableAmount": 89.99,
      "postageDiscount": 0.00,
      "serviceFee": 1.00
    },
    "interceptOrders": [
    ]
  }
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.6 订单列表（GET）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/list?pageNum=1&pageSize=10

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/list?pageNum=1&pageSize=10' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pageNum | 页数 | int | 否 | 20 | 默认 1 |
| pageSize | 每页返回多少条 | int | 否 | 20 | 默认 20 |
| orderIds | 订单ID | List | 否 | 100 | 查询条件 |
| shipmentOrderId | 母订单ID | string | 否 | 100 | 查询条件 |
| status | 订单状态 | string | 否 | 20 | 默认值: CANCELLED, 可选值:CREATED,IN_CART,UNPAID,UNSHIPPED,SHIPPED,DELIVERED,CANCELLED,OTHER |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "orderId": "210823100016290555",
        "orderNum": "api_52f268d40b8d460e82c0683955e63cc9",
        "cjOrderId": null,
        "shippingCountryCode": "US",
        "shippingProvince": "Connecticut",
        "shippingCity": "ftdsr",
        "shippingPhone": "43514123",
        "shippingAddress": "rfdxf rfdesr",
        "shippingCustomerName": "Xu Old",
        "remark": null,
        "orderWeight": 20,
        "orderStatus": "CREATED",
        "orderAmount": 4.25,
        "productAmount": 0.57,
        "postageAmount": 3.68,
        "logisticName": "CJPacket Ordinary",
        "trackNumber": null,
        "createDate": "2021-08-23 11:31:45",
        "paymentDate": null,
        "productList": [
            {
                "vid": "1392053744945991680",
                "quantity": 1,
                "sellPrice": 0.57
            }
        ]
    },
    "requestId": "3adccdcb-d41b-4808-996b-c7c5c833d77d"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| orderId | 订单ID | string | 200 |  |
| orderNum | 订单号 | string | 200 |  |
| cjOrderId | CJ订单ID | string | 200 |  |
| shippingCountryCode | 交易国家 | string | 200 |  |
| shippingProvince | 交易省份 | string | 200 |  |
| shippingCity | 交易城市 | string | 200 |  |
| shippingAddress | 交易地址 | string | 200 |  |
| shippingCustomerName | 交易接收人 | string | 是 | 200 |
| shippingPhone | 交易电话 | string | 200 |  |
| remark | 订单备注 | string | 否 | 500 |
| logisticName | 物流名称 | string | 200 |  |
| trackNumber | 追踪单号 | string | 200 |  |
| trackingUrl | 追踪号轨迹URL | string | 200 |  |
| orderWeight | 订单重量 | int | 200 |  |
| orderAmount | 订单金额 | BigDecimal | （18，2） | 单位：$（美元） |
| productAmount | 商品金额 | BigDecimal | （18，2） | 单位：$（美元） |
| postageAmount | 物流金额 | BigDecimal | （18，2） | 单位：$（美元） |
| orderStatus | 订单状态 | string | 200 | 参考订单状态 |
| createDate | 创建时间 | string | 200 |  |
| paymentDate | 支付时间 | string | 200 |  |
| storeCreateDate | 店铺订单创建时间 | DateTime | 1 | UTC时间, 示例: 2025-03-14 13:21:07 |
| productList |  | list | 200 |  |
| - vid | 变体ID | string | 200 |  |
| - quantity | 数量 | int | 200 |  |
| - sellPrice | 售价 | BigDecimal | （18，2） | 单位：$（美元） |
 订单状态

 | 订单状态 | 状态 |
| --- | --- |
| CREATED | 创建订单 |
| IN_CART | 加入购物车 |
| UNPAID | 未支付 |
| UNSHIPPED | 未发货 |
| SHIPPED | 发货 |
| DELIVERED | 已完成 |
| CANCELLED | 取消 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.7 订单查询（GET）
 a1. Maximum return of 200 data per page.

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/getOrderDetail?orderId=210711100018043276

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/getOrderDetail?orderId=2107111000180432766&features=f1&features=f2' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
####  Request参数
 | 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| orderId | 订单 id | string | 是 | 200 | 支持id: 客户订单id, CJ订单id |
| features | 启用的特性功能 | List | false | 20 | 如果传入相关特性,会启用相关的功能,启动多个特性时, 传入多个features参数 |
 ####  特性枚举
 | 枚举编码 | 说明 |
| --- | --- |
| LOGISTICS_TIMELINESS | 启用查询物流时效,传入该特性枚举后,结果中会返回 logisticsTimeliness |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "orderId": "210823100016290555",
        "orderNum": "api_52f268d40b8d460e82c0683955e63cc9",
        "platformOrderId": "6387689586969",
        "cjOrderId": null,
        "shippingCountryCode": "US",
        "shippingProvince": "Connecticut",
        "shippingCity": "ftdsr",
        "shippingPhone": "43514123",
        "shippingAddress": "rfdxf rfdesr",
        "shippingCustomerName": "Xu Old",
        "remark": null,
        "orderWeight": 20,
        "orderStatus": "CREATED",
        "orderAmount": 4.25,
        "productAmount": 0.57,
        "postageAmount": 3.68,
        "logisticName": "CJPacket Ordinary",
        "trackNumber": null,
        "createDate": "2021-08-23 11:31:45",
        "paymentDate": null,
        "isComplete":1,
        "fromCountryCode":"CN",
        "disputeId": null
        "productList": [
            {
                "vid": "1392053744945991680",
                "quantity": 1,
                "sellPrice": 0.57,
                "podPropertiesInfo": null,
                "lineItemId": "2505170958390976500",
                "storeLineItemId": "16045188153625"
            }
        ]
    },
    "requestId": "3adccdcb-d41b-4808-996b-c7c5c833d77d"
}

```
pod订单查询返回信息

 ```
{
	"code": 200,
	"result": true,
	"message": "Success",
	"data": {
		"orderId": "210823100016290555",
		"orderNum": "api_52f268d40b8d460e82c0683955e63cc9",
		"cjOrderId": null,
		"shippingCountryCode": "US",
		"shippingProvince": "Connecticut",
		"shippingCity": "ftdsr",
		"shippingPhone": "43514123",
		"shippingAddress": "rfdxf rfdesr",
		"shippingCustomerName": "Xu Old",
		"remark": null,
		"orderWeight": 20,
		"orderStatus": "CREATED",
		"orderAmount": 4.25,
		"productAmount": 0.57,
		"postageAmount": 3.68,
		"logisticName": "CJPacket Ordinary",
		"trackNumber": null,
		"createDate": "2021-08-23 11:31:45",
		"paymentDate": null,
		"isComplete": 1,
		"fromCountryCode": "CN",
		"productList": [
			{
				"vid": "1392053744945991680",
				"quantity": 1,
				"sellPrice": 0.57,
				"podPropertiesInfo": null,
                "lineItemId": "2505170958390976500",
                "storeLineItemId": "16045188153625",
				"podPropertiesInfo": {
                    "image": "https://pod-picture.oss-cn.aliyuncs.com/LX/PO-211-12729261699191806-1.jpg",
                    "isFixedCustom": false,
                    "podVersion": 3,
                    "failedList": [],
                    "effectImgList": [
                        "https://pod-picture.oss-cn.aliyuncs.com/LX/PO-211-1.jpg?podThumbnailUrl=https%3A%2F%2Fpod-picture.oss-cn.aliyuncs.com%2Fpod%2F250428%2Fpod-picture_oss-cn-211-12729261699191806-1_jpg.1440x1440.webp&podOriginSize=638820&podOriginPxUrl=https%3A%2F%2Fpod-picture.oss-cn-hangzhou.aliyuncs.com%2Fpod_infinity%2F250428%2Fpod-picture_oss-cn-hangzhou_aliyuncs_com_LX_PO-211-12729261699191806-1_jpg.InfinityxInfinity.webp&podOriginPx=1936_1854&podOriginOss=https%3A%2F%2Fpod-picture.oss-cn-hangzhou.aliyuncs.com%2Fpod_origin%2F250428%2Fpod-picture_oss-cn-hangzhou_aliyuncs_com_LX_PO-211-1_jpg.InfinityxInfinity.jpg"
                    ],
                    "finish": 1,
                    "customResources": [],
                    "type": 5,
                    "customMessgae": {
                        "podType": 1,
                        "color": {},
                        "zone": {
                            "back": {},
                            "front": {}
                        }
                    },
                    "productionImgList": [
                        "https://pod-picture.oss-cn.aliyuncs.com/LX/PO-211-1.jpg?podThumbnailUrl=https%3A%2F%2Fpod-picture.oss.aliyuncs.com%2Fpod%2F250428%2Fpod-picture_oss-cn-hangzhou_aliyuncs_com_LX_PO-211-12729261699191806-1_jpg.1440x1440.webp&podOriginSize=638820&podOriginPxUrl=https%3A%2F%2Fpod-picture.oss-cn-hangzhou.aliyuncs.com%2Fpod_infinity%2F250428%2Fpod-picture_oss-cn-hangzhou_aliyuncs_com_LX_PO-211-12729261699191806-1_jpg.InfinityxInfinity.webp&podOriginPx=1936_1854&podOriginOss=https%3A%2F%2Fpod-picture.oss-cn-hangzhou.aliyuncs.com%2Fpod_origin%2F250428%2Fpod-picture_oss-cn-hangzhou_aliyuncs_com_LX_PO-211-12729261699191806-1_jpg.InfinityxInfinity.jpg"
                    ],
                    "customDesign": [
                        {
                            "img": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/180af06e-7b7-4662-b975-070203989480.jpg",
                            "areaNameEn": "",
                            "printWidth": "50",
                            "typeName": "",
                            "type": "1",
                            "scaleX": "1",
                            "backImgList": [
                                {
                                    "color": "1pcs",
                                    "imgSrc": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/00e2483-b3b2-4873-80ac-e71f4d760e1f.jpg"
                                },
                                {
                                    "color": "4pcs",
                                    "imgSrc": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/0c42181-d63f-49f9-b6d5-d55574027fcb.jpg"
                                },
                                {
                                    "color": "10pcs",
                                    "imgSrc": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/1ae2f95-5484-4d30-a93f-64bc740832d2.jpg"
                                },
                                {
                                    "color": "16pcs",
                                    "imgSrc": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/53ce421-33db-4249-8862-f36ad20083b5.jpg"
                                },
                                {
                                    "color": "18pcs",
                                    "imgSrc": "https://oss-cf.cjdropshipping.com/product/2025/04/22/01/245e348-a87b-4196-a3a4-056f6b391301.jpg"
                                }
                            ],
                            "printHeight": "50",
                            "scaleY": "1",
                            "podType": "4",
                            "top": "297.99999928474426",
                            "areaName": "DIY",
                            "left": "253.99999994039536",
                            "areaType": "1",
                            "imgicon": "",
                            "angle": "0",
                            "fontSize": 12,
                            "fontSpace": 0,
                            "sku": ""
                        }
                    ]
                }
			}
		]
	},
	"requestId": "3adccdcb-d41b-4808-996b-c7c5c833d77d"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| orderId | CJ订单ID | string | 200 |  |
| orderNum | 店铺订单号 | string | 200 |  |
| platformOrderId | 店铺订单Id | string | 200 |  |
| fromCountryCode | 发货国家编码 | string | 2 |  |
| shippingCountryCode | 收货人国家编码 | string | 200 |  |
| shippingProvince | 收货人省份 | string | 200 |  |
| shippingCity | 收货人城市 | string | 200 |  |
| shippingAddress | 收货人地址 | string | 200 |  |
| shippingCustomerName | 收货人名称 | string | 是 | 200 |
| shippingPhone | 收货人电话 | string | 200 |  |
| remark | 订单备注 | string | 否 | 500 |
| logisticName | 物流名称 | string | 200 |  |
| trackNumber | 追踪单号 | string | 200 |  |
| trackingUrl | 追踪号轨迹URL | string | 200 |  |
| disputeId | CJ纠纷id | string | 50 |  |
| orderWeight | 订单重量 | int | 200 |  |
| orderAmount | 订单金额 | BigDecimal | （18，2） | 单位：$（美元） |
| productAmount | 商品金额 | BigDecimal | （18，2） | 单位：$（美元） |
| postageAmount | 物流金额 | BigDecimal | （18，2） | 单位：$（美元） |
| orderStatus | 订单状态 | string | 200 | 参考订单状态 |
| createDate | 创建时间 | string | 200 | UTC时间 |
| paymentDate | 支付时间 | string | 200 | UTC时间 |
| outWarehouseTime | 出库时间 | DateTime | 1 | UTC时间, 示例: 2025-03-14 13:21:07 |
| storeCreateDate | 店铺订单创建时间 | DateTime | 1 | UTC时间, 示例: 2025-03-14 13:21:07 |
| isComplete | 订单是否完整1:完整 0:不完整 | Number | 1 |  |
| productList | 订单中的商品 | list | 200 |  |
| - vid | 变体ID | string | 200 |  |
| - quantity | 数量 | int | 200 |  |
| - sellPrice | 售价 | BigDecimal | （18，2） | 单位：$（美元） |
| - storeLineItemId | 店铺订单的lineItemId | string | 125 |  |
| - lineItemId | CJ订单item的唯一id | string | 50 |  |
| - podPropertiesInfo | pod订单信息 | Object |  |  |
| -- effectImgList | 效果图 | string | 200 |  |
| -- customResources | 成品信息 | string | 200 |  |
| -- productionImgList | 生产图 | string | 200 |  |
| logisticsTimeliness | 物流时效 | Object |  |  |
| - logisticsModes | 物流公司列表 | List |  |  |
| -- logisticsName | 物流名称 | string |  | DHL Official |
| -- arrivalTime | 妥投天数 | string |  | 3-7 Days |
 订单状态

 | 订单状态 | 状态 |
| --- | --- |
| CREATED | 创建订单 |
| IN_CART | 加入购物车 |
| UNPAID | 未支付 |
| UNSHIPPED | 未发货 |
| SHIPPED | 发货 |
| DELIVERED | 已完成 |
| CANCELLED | 取消 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ####  错误码
 | 错误码 | 错误信息 |
| --- | --- |
| 1600300 | order not found |
| 1600300 | orderId must be not empty |
| 1600300 | The maximum number of features is 20 |
 ###  1.8 订单删除（DEL）
 确认订单后则无法删除

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/deleteOrder?orderId=210711100018655344

 ####  CURL
 ```
curl --location --request DELETE 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/deleteOrder?orderId=210711100018655344' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| orderId | 订单 id | string | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": "210711100018655344",
    "requestId": "721341bf-abf8-4d8c-b400-1fbdaef79039"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回(订单号) |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.9 订单确认（PATCH）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/order/confirmOrder

 ####  CURL
 ```
curl --location --request PATCH 'https://developers.cjdropshipping.com/api2.0/v1/shopping/order/confirmOrder' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "orderId": "210711100018655344"
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| orderId | 订单 id | string | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": "210711100018655344",
    "requestId": "721341bf-abf8-4d8c-b400-1fbdaef79039"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回(订单号) |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
    "code": 1603001,
    "result": false,
    "message": "order confirm fail",
    "data": null,
    "requestId": "7dc61955-c0e8-4731-bb9b-393b4fffeaaf"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ##  2 支付
 ###  2.1 余额查询（GET）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/getBalance

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/getBalance' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "amount": 87247.32,
        "noWithdrawalAmount": 0.00,
        "freezeAmount": 0.00
    },
    "requestId": "36fc030a-a110-4318-bc83-f39f9d3e5484"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| amount | 余额 | string | 200 | 末尾2位小数点 |
| noWithdrawalAmount | 未支付金额 | BigDecimal | （18，2） | 单位：$（美元） |
| freezeAmount | 冻结金额 | BigDecimal | （18，2） | 单位：$（美元） |
 error

 ```
{
   "code": 1600100,
   "result": false,
   "message": "Param error",
   "data": null,
   "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  2.2 余额支付（POST）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/payBalance

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/payBalance' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "orderId": "210711100018655344"
                }'

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| orderId | 订单 | string | 200 |  |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": 12,
    "requestId": "7dbe69b9-dd82-4ee3-907c-a6fca833e3ce"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回（订单号） |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  2.3 余额支付V2（POST）
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/payBalanceV2

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/shopping/pay/payBalanceV2' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "shipmentOrderId": "12",
                    "payId": "12"
                }'

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| shipmentOrderId | 母订单id | string | 200 |  |
| payId | payId | string | 200 |  |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": 12,
    "requestId": "7dbe69b9-dd82-4ee3-907c-a6fca833e3ce"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回（订单号） |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |


---

#  3 商品模块
 ##  1 商品
 ###  1.1 类目(GET)
 获取CJ商品类目

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/getCategory

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/getCategory' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
####  Return
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": [
        {
            "categoryFirstName": "Computer & Office",
            "categoryFirstList": [
                {
                    "categorySecondName": "Office Electronics",
                    "categorySecondList": [
                        {
                            "categoryId": "2252588B-72E3-4397-8C92-7D9967161084",
                            "categoryName": "Office & School Supplies"
                        },
                    ]...
                }
            ]    
        }
    ],
    "requestId": "ae543fd1-cdd7-4a61-974a-1340fea678c6"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| categoryFirstName | 一级目录名称 | string | 200 |  |
| categoryFirstList | list | string | 200 |  |
| categorySecondName | 二级目录名称 | string | 200 |  |
| categorySecondList | list | string | 200 |  |
| categoryId | 三级类目id | string | 200 |  |
| categoryName | 三级类目名称 | string | 200 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 业务数据 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.2 商品列表V2(GET)
 获取所有 CJ 线上有效商品，支持条件查询。V2版本使用elasticsearch搜索引擎，提供更高性能的商品搜索能力。

 注：

 - 支持关键词搜索
 - 支持价格区间、类目、国家等多条件筛选
 - 支持排序功能
 - 通过features参数可选择性返回商品详情和类目信息
 - page最小值1，最大值1000；size最小值1，最大值100
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/listV2

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/listV2?page=1&size=20&keyWord=hoodie' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| keyWord | 搜索关键词 | string | 否 | 200 | 商品名称或SKU关键词搜索 |
| page | 页码 | int | 否 | 20 | 默认 1，最小1，最大1000 |
| size | 每页返回多少条 | int | 否 | 20 | 默认 10，最小1，最大100 |
| categoryId | 类目ID | string | 否 | 200 | 根据商品三级类目ID筛选商品 |
| lv2categoryList | 二级类目ID列表 | array | 否 |  | 根据二级类目ID列表筛选商品 |
| lv3categoryList | 三级类目ID列表 | array | 否 |  | 根据三级类目ID列表筛选商品 |
| countryCode | 国家代码 | string | 否 | 200 | 格式: CN,US,GB,FR 等，筛选在指定国家有库存的商品 |
| startSellPrice | 起始价格 | decimal | 否 |  | 价格筛选起始值 |
| endSellPrice | 结束价格 | decimal | 否 |  | 价格筛选结束值 |
| addMarkStatus | 是否包邮 | int | 否 | 1 | 0-不包邮 1-包邮 |
| productType | 商品类型 | int | 否 | 15 | 4-供应商商品 10-视频商品 11-非视频商品 |
| productFlag | 商品标识 | int | 否 | 1 | 0-趋势商品 1-最新商品 2-视频商品 3-滞销商品 |
| startWarehouseInventory | 仓库起始库存 | int | 否 |  | 筛选库存数量大于等于该值的商品 |
| endWarehouseInventory | 仓库结束库存 | int | 否 |  | 筛选库存数量小于等于该值的商品 |
| verifiedWarehouse | 验证库存类型 | int | 否 | 1 | null/0-全部(默认) 1-验证库存 2-待验证库存 |
| timeStart | 上架时间筛选开始时间 | long | 否 |  | 上架时间筛选的开始时间戳（毫秒） |
| timeEnd | 上架时间筛选结束时间 | long | 否 |  | 上架时间筛选的结束时间戳（毫秒） |
| zonePlatform | 专区建议销售平台 | string | 否 | 200 | 如：shopify,ebay,amazon,tiktok,etsy 等 |
| isWarehouse | 是否全球仓搜索 | boolean | 否 | 1 | true-是 false-否 |
| currency | 币种 | string | 否 | 10 | 如：USD,AUD,EUR 等 |
| sort | 排序方向 | string | 否 | 4 | desc-降序(默认) / asc-升序 |
| orderBy | 排序字段 | int | 否 | 20 | 0=最匹配(默认); 1=刊登数量; 2=销售价格; 3=创建时间; 4=库存 |
| features | 特性集合 | array | 否 | 200 | 支持值: enable_description(返回商品详情), enable_category(返回商品类目信息), enable_combine(返回组合商品信息), enable_video(返回视频ID) |
| supplierId | 供应商ID | string | 否 | 200 | 根据供应商ID筛选商品 |
| hasCertification | 是否有资质 | int | 否 | 1 | 0-无 1-有 |
| isSelfPickup | 是否支持自提 | int | 否 | 1 | 0-否 1-是 |
| customization | 是否定制商品 | int | 否 | 1 | 0-否 1-是 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "pageSize": 20,
        "pageNumber": 1,
        "totalRecords": 1000,
        "totalPages": 50,
        "content": [
            {
                "productList": [
                    {
                        "id": "04A22450-67F0-4617-A132-E7AE7F8963B0",
                        "nameEn": "Personalized Belly-baring Cat Ear Hoody Coat",
                        "sku": "CJNSSYWY01847",
                        "spu": "CJNSSYWY01847",
                        "bigImage": "https://cc-west-usa.oss-us-west-1.aliyuncs.com/20210129/2167381084610.png",
                        "sellPrice": "11.85",
                        "nowPrice": "9.50",
                        "listedNum": 100,
                        "categoryId": "5E656DFB-9BAE-44DD-A755-40AFA2E0E686",
                        "threeCategoryName": "Hoodies & Sweatshirts",
                        "twoCategoryId": "5E656DFB-9BAE-44DD-A755-40AFA2E0E685",
                        "twoCategoryName": "Tops & Sets",
                        "oneCategoryId": "5E656DFB-9BAE-44DD-A755-40AFA2E0E684",
                        "oneCategoryName": "Women's Clothing",
                        "addMarkStatus": 1,
                        "isVideo": 0,
                        "videoList": [],
                        "productType": "ORDINARY_PRODUCT",
                        "supplierName": "",
                        "createAt": 1609228800000,
                        "warehouseInventoryNum": 500,
                        "totalVerifiedInventory": 500,
                        "totalUnVerifiedInventory": 0,
                        "verifiedWarehouse": 1,
                        "customization": 0,
                        "hasCECertification": 0,
                        "isCollect": 0,
                        "myProduct": false,
                        "currency": "USD",
                        "discountPrice": "9.50",
                        "discountPriceRate": "20",
                        "description": "商品详情描述...",
                        "deliveryCycle": "3-5",
                        "saleStatus": "3",
                        "authorityStatus": "1",
                        "isPersonalized": 0
                    }
                ],
                "relatedCategoryList": [
                    {
                        "categoryId": "xxx",
                        "categoryName": "Hoodies"
                    }
                ],
                "categoryList": [
                    {
                        "categoryId": "xxx",
                        "categoryName": "Women's Clothing"
                    }
                ],
                "storeList": [
                    {
                        "warehouseId": "1",
                        "warehouseName": "China Warehouse",
                        "countryCode": "CN"
                    }
                ],
                "keyWord": "hoodie",
                "keyWordOld": "hoodie",
                "searchHit": "1::1000"
            }
        ]
    },
    "requestId": "f95cd31d-3907-47ce-ac1a-dfdee4315960"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| pageSize | 每页数量 | long | 20 | 每页商品数量 |
| pageNumber | 当前页码 | long | 20 | 当前请求的页码，从1开始 |
| totalRecords | 总记录数 | long | 20 | 符合条件的商品总数 |
| totalPages | 总页数 | long | 20 | 总页数 |
| content | 内容列表 | array |  | 商品数据列表 |
 content中的CjProductInfoSearchV2DTO对象说明：

 | 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| productList | 商品列表 | array |  | 商品信息数组 |
| relatedCategoryList | 关联类目列表 | array |  | 搜索关键词匹配到的相关类目列表 |
| categoryList | 类目列表 | array |  | 商品所属类目树列表（仅当features包含enable_category时返回） |
| storeList | 仓库列表 | array |  | 可用仓库信息列表 |
| authNum | 授权商品数量 | int | 20 | 查询阿里商品数量 |
| keyWord | 搜索关键词 | string | 200 | 实际使用的搜索关键词 |
| keyWordOld | 原始搜索关键词 | string | 200 | 用户输入的原始搜索关键词 |
| searchHit | 搜索结果统计 | string | 200 | 格式: 1::数量 |
| b | 是否包含禁用词 | boolean | 1 | true-包含 false-不包含 |
 productList中的商品对象说明：

 | 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| id | 商品ID | string | 200 | 商品唯一标识符 |
| nameEn | 商品英文名称 | string | 200 | 商品英文名称 |
| sku | 商品SKU | string | 200 | 商品SKU编码 |
| spu | 商品SPU | string | 200 | 商品SPU编码，与SKU相同 |
| bigImage | 商品主图 | string | 200 | 商品主图URL |
| sellPrice | 售价 | string | 20 | 商品售价，单位：美元 |
| nowPrice | 折扣价 | string | 20 | 商品折扣价格 |
| discountPrice | 最优折扣价格 | string | 20 | 最优折扣价格 |
| discountPriceRate | 折扣率 | string | 20 | 折扣百分比 |
| listedNum | 刊登数量 | int | 20 | 商品在平台的刊登数量 |
| isCollect | 是否收藏 | int | 1 | 0-未收藏 1-已收藏 |
| categoryId | 三级类目ID | string | 200 | 商品所属三级类目ID |
| threeCategoryName | 三级类目名称 | string | 200 | 三级类目名称（仅当features包含enable_category时返回） |
| twoCategoryId | 二级类目ID | string | 200 | 商品所属二级类目ID |
| twoCategoryName | 二级类目名称 | string | 200 | 二级类目名称（仅当features包含enable_category时返回） |
| oneCategoryId | 一级类目ID | string | 200 | 商品所属一级类目ID |
| oneCategoryName | 一级类目名称 | string | 200 | 一级类目名称（仅当features包含enable_category时返回） |
| addMarkStatus | 是否包邮 | int | 1 | 0-不包邮 1-包邮 |
| isVideo | 是否有视频 | int | 1 | 0-无视频 1-有视频 |
| videoList | 视频ID列表 | array |  | 商品视频ID集合（仅当features包含enable_video时返回） |
| productType | 商品类型 | string | 200 | 商品类型代码 |
| supplierName | 供应商名称 | string | 200 | 商品供应商名称 |
| createAt | 创建时间 | long | 20 | 商品创建时间戳（毫秒） |
| setRecommendedTime | 推荐时间 | long | 20 | 设置推荐的时间戳 |
| warehouseInventoryNum | 仓库库存数量 | long | 20 | 商品总库存数量 |
| totalVerifiedInventory | 总验证库存 | int | 20 | 已验证的库存总数 |
| totalUnVerifiedInventory | 总未验证库存 | int | 20 | 待验证的库存总数 |
| verifiedWarehouse | 验证库存标识 | int | 1 | 1-已验证库存 2-待验证库存 |
| customization | 是否定制商品 | int | 1 | 0-否 1-是 |
| isPersonalized | 是否个性化定制 | int | 1 | 0-否 1-是 |
| hasCECertification | 是否有CE认证 | int | 1 | 0-否 1-是 |
| myProduct | 是否已添加到我的商品 | boolean | 1 | true-已添加 false-未添加 |
| currency | 币种 | string | 10 | 如：USD, AUD, EUR等 |
| description | 商品详情 | string | 2000 | 商品详细描述（仅当features包含enable_description时返回） |
| deliveryCycle | 到货周期 | string | 20 | 商品到货周期，单位：天 |
| saleStatus | 上下架状态 | string | 2 | 3-审核通过可销售 |
| authorityStatus | 用户可见权限 | string | 1 | 0-私有可见 1-全部可见 |
| autStatus | 商品可见性 | string | 1 | 商品可见性状态 |
| isAut | 是否永久私有 | string | 1 | 0-非永久私有 1-永久私有 |
| isList | 是否已刊登 | int | 1 | 0-未刊登 1-已刊登 |
| syncListedProductStatus | 刊登状态 | string | 1 | 0-待刊登 1-刊登中 2-刊登失败 3-刊登成功 4-取消刊登 |
| isAd | 是否广告商品 | int | 1 | 0-非广告 1-广告商品 |
| activityId | 广告商品ID | string | 200 | 广告活动ID |
| directMinOrderNum | 起批量 | string | 20 | 最小起订量 |
| zoneRecommendJson | 分区推荐列表 | set |  | 专区推荐标识集合 |
| inventoryInfo | 各仓库存信息 | string |  | 各个仓库的库存详情JSON |
| variantKeyEn | 变体属性 | string | 200 | 变体属性英文描述 |
| variantInventories | 变体库存信息 | string |  | 变体库存详情JSON |
| propertyKey | 商品物流属性key | string | 200 | 商品物流属性关键词 |
 商品类型 productType

 | 商品类型 | 类型意义 | 备注 |
| --- | --- | --- |
| ORDINARY_PRODUCT | 普通商品，CJ管理库存的商品 | 由CJ直接管理库存和发货 |
| SERVICE_PRODUCT | 服务商品，是你如果需要将你自己的商品转存入CJ仓库，由CJ提供仓储服务时，我们将它会标记为服务商品； | 用户自己的商品，由CJ提供仓储服务 |
| PACKAGING_PRODUCT | 包装商品，在仓库发货时用于包装，他不支持单独代发，需要和其他商品一起发货； | 仅用于包装，不可单独销售 |
| SUPPLIER_PRODUCT | 供应商商品，供应商的商品，但由CJ管理库存与发货 | 供应商提供，CJ代销代发 |
| SUPPLIER_SHIPPED_PRODUCT | 供应商自发货商品，供应商的商品，由供管商管理库存与发货 | 供应商提供并发货 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 业务数据 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.3 全球仓库列表(GET)
 获取所有可用的全球仓库信息列表。

 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/globalWarehouseList

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/globalWarehouseList' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
####  请求参数
 无需参数

 ####  返回
 success

 ```
{
    "code": 200,
    "success": true,
    "message": "Success",
    "data": [
        {
            "areaCn": "中国仓",
            "areaEn": "China Warehouse",
            "areaId": 1,
            "countryCode": "CN",
            "nameEn": "China",
            "valueEn": "CN",
            "disabled": false,
            "zh": "中国仓",
            "en": "China Warehouse",
            "de": "China-Lager",
            "fr": "Entrepôt Chine",
            "th": "คลังสินค้าจีน",
            "id": "1"
        },
        {
            "areaCn": "美国仓",
            "areaEn": "US Warehouse",
            "areaId": 2,
            "countryCode": "US",
            "nameEn": "United States",
            "valueEn": "US",
            "disabled": false,
            "zh": "美国仓",
            "en": "US Warehouse",
            "de": "US-Lager",
            "fr": "Entrepôt américain",
            "th": "คลังสินค้าสหรัฐ",
            "id": "2"
        }
    ],
    "requestId": "ae543fd1-cdd7-4a61-974a-1340fea678c6"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| areaCn | 仓库中文名称 | string | 200 | 仓库的中文名称 |
| areaEn | 仓库英文名称 | string | 200 | 仓库的英文名称 |
| areaId | 仓库ID | int | 20 | 仓库唯一标识 |
| countryCode | 国家代码 | string | 10 | ISO国家代码，如：CN、US、GB等 |
| nameEn | 国家英文名称 | string | 200 | 国家的英文名称 |
| valueEn | 仓库代码 | string | 10 | 仓库代码值，通常与国家代码一致 |
| disabled | 是否禁用 | boolean | 1 | true-禁用，false-可用 |
| zh | 中文名称 | string | 200 | 多语言支持-中文 |
| en | 英文名称 | string | 200 | 多语言支持-英文 |
| de | 德语名称 | string | 200 | 多语言支持-德语 |
| fr | 法语名称 | string | 200 | 多语言支持-法语 |
| th | 泰语名称 | string | 200 | 多语言支持-泰语 |
| id | 仓库字符串ID | string | 20 | 仓库ID的字符串形式 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 业务数据 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.4 商品列表(GET)
 获取所有 CJ 线上有效商品，支持条件查询。

 注：

 - 最大每页返回 200条数据
 - 普通用户或v1用户一天最大请求1000次（2024-09-30 更新）
 - 一个ip限制最多3个用户（2024-09-30 更新）
 - 查询商品列表入参增加"deliveryTime"（发货时效），值为24,48,72或者不传。(2024-11-15 更新)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/list

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/list' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pageNum | 页数 | int | 否 | 20 | 默认 1，指定要获取的商品列表页码 |
| pageSize | 每页返回多少条 | int | 否 | 20 | 默认 20，每页返回的商品数量，最大200 |
| categoryId | 种类ID | string | 否 | 200 | 查询条件，根据商品类目ID筛选商品 |
| pid | 商品 id | string | 否 | 200 | 根据商品唯一标识符筛选商品 |
| productSku | 商品SKU | string | 否 | 200 | 根据商品SKU筛选商品 |
| productType | 商品类型 | string | 否 | 15 | 可选值: ORDINARY_PRODUCT(普通商品)、SUPPLIER_PRODUCT(供应商商品)，不传则返回所有类型 |
| productName | 商品名称 | string | 否 | 100 | 根据商品中文名称模糊匹配 |
| productNameEn | 商品名称英文 | string | 否 | 100 | 根据商品英文名称模糊匹配 |
| deliveryTime | 发货时效（小时） | string | 否 | 100 | 可选值: 24(24小时发货)、48(48小时发货)、72(72小时发货)，只返回满足指定时效的商品 |
| verifiedWarehouse | 验证库存类型 | number | 否 | 1 | 可选值: 1(已验证库存)、2(未验证库存)，不传值表示不限制 |
| startInventory | 查询最低库存 | number | 否 |  | 格式: 2，筛选库存数量大于等于该值的商品 |
| endInventory | 查询最高库存 | number | 否 |  | 格式: 10，筛选库存数量小于等于该值的商品 |
| createTimeFrom | 开始创建时间 | Date | 否 |  | 格式: yyyy-MM-dd hh:mm:ss，筛选该时间之后创建的商品 |
| createTimeTo | 结束创建时间 | Date | 否 |  | 格式: yyyy-MM-dd hh:mm:ss，筛选该时间之前创建的商品 |
| minPrice | 最低价格 | number | 否 |  | 格式: 1.0，筛选商品价格大于等于该值的商品 |
| maxPrice | 最高价格 | number | 否 |  | 格式: 2.0，筛选商品价格小于等于该值的商品 |
| countryCode | 商品所在发货国家 | string | 否 |  | 格式: CN,US，筛选在指定国家有库存的商品 |
| searchType | 搜索类型 | number | 否 | 5 | 可选值: 0(全部商品)、2(热门商品Trending Product)、21(更多热门商品Trending Product View More)，默认值为0 |
| minListedNum | 最小刊登数量 | number | 否 | 10 | 示例: 1，返回刊登数量大于等于该值的商品 |
| maxListedNum | 最大刊登数量 | number | 否 | 10 | 示例: 10，返回刊登数量小于等于该值的商品 |
| sort | 排序类型 | string | 否 | 4 | 可选值: desc(降序排列)、asc(升序排列)，默认值为desc |
| orderBy | 排序字段 | string | 否 | 20 | 可选值: createAt(按创建时间排序)、listedNum(按刊登数量排序)，默认值为createAt |
| isSelfPickup | 商品是否支持自提 | number | 否 | 1 | 可选值: 1(支持自提)、0(不支持自提) |
| supplierId | 供应商id | string | 否 | 40 | 根据供应商ID筛选商品 |
| isFreeShipping | 是否包邮 | int | 否 | 1 | 可选值: 0(不包邮)、1(包邮) |
| customizationVersion | 定制版本 | int | 否 | 1 | 可选值: 1(平台定制版本V1)、2(平台定制版本V2)、3(客户定制版本V1)、4(客户定制版本V2)、5(POD 3.0平台定制)，筛选指定定制版本的POD商品 |
 ####  返回
 success

 ```
{
     "code": 200,
     "result": true,
     "message": "Success",
     "data": {
         "pageNum": 1,
         "pageSize": 20,
         "total": 1,
         "list": [
             {
                 "pid": "04A22450-67F0-4617-A132-E7AE7F8963B0",
                 "productName": "[\"猫耳朵卫衣\",\"定制卫衣\",\"个性化定制\"]",
                 "productNameEn": "Personalized Belly-baring Cat Ear Hoody Coat",
                 "productSku": "CJNSSYWY01847",
                 "productImage": "https://cc-west-usa.oss-us-west-1.aliyuncs.com/20210129/2167381084610.png",
                 "productWeight": 0,
                 "productType": null,
                 "productUnit": "unit(s)",
                 "sellPrice": 11.85,
                 "categoryId": "5E656DFB-9BAE-44DD-A755-40AFA2E0E686",
                 "categoryName": "Women's Clothing / Tops & Sets / Hoodies & Sweatshirts",
                 "remark": "",
                 "createTime": null
             }
         ]
     },
     "requestId": "f95cd31d-3907-47ce-ac1a-dfdee4315960"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| pageNum | 当前页数 | int | 20 | 当前请求的页码 |
| pageSize | 每页返回多少条 | int | 20 | 每页商品数量 |
| total | 总条数 | int | 20 | 符合条件的商品总数 |
| list | 商品列表 | Product[] |  | 商品数据列表 |
| pid | 商品 Id | string | 200 | 商品唯一标识符 |
| productName | 商品名称 | string | 20 | 商品中文名称，可能包含多个名称的JSON数组 |
| productNameEn | 商品名称(英文) | string | 200 | 商品英文名称 |
| productSku | 商品SKU | string | 200 | 商品SKU编码 |
| productImage | 商品主图 | string | 200 | 商品主图URL |
| productWeight | 商品重量 | int | 200 | 单位: g |
| productType | 商品类型 | byte | 200 | 商品类型代码 |
| productUnit | 商品单位 | string | 48 | 商品售卖单位 |
| isVideo | 是否包含商品视频 | string | 200 | 1表示包含视频，0表示不包含 |
| saleStatus | 商品上架状态 | int | 20 | 3表示审核通过可销售 |
| listedNum | 商品刊登数量 | int | 200 | 该商品在平台上的刊登数量 |
| supplierName | 供应商名称 | string | 200 | 商品供应商名称 |
| supplierId | 供应商id | string | 200 | 商品供应商ID |
| categoryId | 种类id | string | 200 | 商品所属类目ID |
| categoryName | 种类名称 | string | 200 | 商品所属类目名称 |
| remark | 备注 | string | 200 | 商品备注信息 |
| addMarkStatus | 是否包邮? 已过期, 请使用 isFreeShipping | int | 1 | 0=Not free shipping, 1=free shipping |
| isFreeShipping | 是否包邮? | boolean | 1 | true表示包邮，false表示不包邮 |
| createTime | 创建时间 | string |  | 商品在平台的创建时间 |
| customizationVersion | 定制版本 | int | 1 | 定制商品版本号 |
 商品类型 productType

 | 商品类型 | 类型意义 | 备注 |
| --- | --- | --- |
| ORDINARY_PRODUCT | 普通商品，CJ管理库存的商品 | 由CJ直接管理库存和发货 |
| SERVICE_PRODUCT | 服务商品，是你如果需要将你自己的商品转存入CJ仓库，由CJ提供仓储服务时，我们将它会标记为服务商品； | 用户自己的商品，由CJ提供仓储服务 |
| PACKAGING_PRODUCT | 包装商品，在仓库发货时用于包装，他不支持单独代发，需要和其他商品一起发货； | 仅用于包装，不可单独销售 |
| SUPPLIER_PRODUCT | 供应商商品，供应商的商品，但由CJ管理库存与发货 | 供应商提供，CJ代销代发 |
| SUPPLIER_SHIPPED_PRODUCT | 供应商自发货商品，供应商的商品，由供管商管理库存与发货 | 供应商提供并发货 |
 商品状态 productStatus

 | 商品状态值 | 类型意义 |
| --- | --- |
| 3 | 审核通过 |
 定制版本

 | 定制版本 | 类型意义 |
| --- | --- |
| 0 | 非pod商品 |
| 1 | 平台定制版本V1 |
| 2 | 平台定制版本V2 |
| 3 | 客户定制版本V1 |
| 4 | 客户定制版本V2 |
| 5 | POD3.0平台定制 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.3 商品详情(GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/query

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/query?pid=000B9312-456A-4D31-94BD-B083E2A198E8' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pid | 商品 id | string | pid、productSku、variantSku三选一 | 200 | 查询条件，商品唯一标识符 |
| productSku | 商品 SKU | string | pid、productSku、variantSku三选一 | 200 | 查询条件，商品SKU编码 |
| variantSku | 变体 SKU | string | pid、productSku、variantSku三选一 | 200 | 查询条件，商品变体SKU编码 |
| features | 特性集合 | string[] | 否 | 200 | 可选值: enable_combine(支持组合，传入则返回组合商品信息)、enable_video(包含视频，传入则返回商品视频信息) |
| countryCode | 库存所在国家 | string | 否 | 2 | 国家代码，如CN、US，只返回在该国家有库存的变体，不传值则不限制 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "pid": "000B9312-456A-4D31-94BD-B083E2A198E8",
        "productName": "[\"攀爬车 拖斗车 \",\"攀爬车 \",\"拖斗车 \"]",
        "productNameEn": "Small trailer model",
        "productSku": "CJJJJTJT05843",
        "productImage": "https://cc-west-usa.oss-us-west-1.aliyuncs.com/2054/1672872416690.jpg",
        "productWeight": "1500.0",
        "productUnit": "unit(s)",
        "productType": "ORDINARY_PRODUCT",
        "categoryId": "87CF251F-8D11-4DE0-A154-9694D9858EB3",
        "categoryName": "Home & Garden, Furniture / Home Storage / Home Office Storage",
        "entryCode": "8712008900",
        "entryName": "模型",
        "entryNameEn": "model",
        "materialName": "[\"\",\"金属\"]",
        "materialNameEn": "[\"\",\"metal\"]",
        "materialKey": "[\"METAL\"]",
        "packingWeight": "1580.0",
        "packingName": "[\"\",\"塑料袋\"]",
        "packingNameEn": "[\"\",\"plastic_bag\"]",
        "packingKey": "[\"PLASTIC_BAG\"]",
        "productKey": "[\"颜色\"]",
        "productKeyEn": "Color",
        "productPro": "[\"普货\"]",
        "productProSet": ["普货"],
        "productProEn": "[\"COMMON\"]",
        "productProEnSet": ["COMMON"],
        "sellPrice": 58.09,
        "productVideo": [],
        "status": 1,
        "productSugSellPrice": 58.09,
        "variatListQuantity": 10,
        "supplierName": "",
        "supplierId": ""
        "description": "....",
        "customizationVersion": 1,
        "customizationJson1": "",
        "customizationJson2": "",
        "customizationJson3": "",
        "customizationJson4": "",
        "variants": [
            {
                "vid": "D4057F56-3F09-4541-8461-9D76D014846D",
                "pid": "000B9312-456A-4D31-94BD-B083E2A198E8",
                "variantName": null,
                "variantNameEn": "Small trailer model Black",
                "variantSku": "CJJJJTJT05843-Black",
                "image": ""
                "variantUnit": null,
                "variantProperty": null,
                "variantKey": "Black",
                "variantLength": 300,
                "variantWidth": 200,
                "variantHeight": 100,
                "variantVolume": 6000000,
                "variantWeight": 1580.00,
                "variantSellPrice": 58.09,
                "variantSugSellPrice": 58.09,
                "createTime": "2019-12-31T11:14:12.000+00:00"
            }...
        ],
        "createrTime": "2019-12-24T01:06:37+08:00"
    },
    "requestId": "13631757-39b5-496f-bcd0-5fa192d6fa24"
}

```
product

 | 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| pid | 商品 Id | string | 200 | 商品唯一标识符 |
| productName | 商品名称 | string | 20 | 商品中文名称，JSON数组格式 |
| productNameEn | 商品名称(英文) | string | 200 | 商品英文名称 |
| productSku | 商品SKU | string | 200 | 商品SKU编码 |
| productImage | 商品图像 | string | 200 | 商品主图URL |
| productWeight | 商品重量 | int | 200 | 单位: g |
| productType | 商品类型 | byte | 200 | 商品类型代码 |
| productUnit | 商品单位 | string | 48 | 商品售卖单位 |
| categoryId | 种类id | string | 200 | 商品所属类目ID |
| categoryName | 种类名称 | string | 200 | 商品所属类目名称 |
| entryCode | 海关代码 | string | 200 | 商品海关编码 |
| entryName | 海关名称 | string | 200 | 商品海关中文名称 |
| entryNameEn | 海关名称(英文) | string | 200 | 商品海关英文名称 |
| materialName | 材料名称 | string | 200 | 商品材料中文名称 |
| materialNameEn | 材料名称(英文) | string | 200 | 商品材料英文名称 |
| materialKey | 材料属性 | string | 200 | 商品材料属性关键词 |
| packingWeight | 包装重量 | int | 200 | 单位: g，包装后总重量 |
| packingName | 包装名称 | string | 200 | 包装材料中文名称 |
| packingNameEn | 包装名称(英文) | string | 200 | 包装材料英文名称 |
| packingKey | 包装属性 | string | 200 | 包装材料属性关键词 |
| productKey | 商品属性 | string | 200 | 商品属性关键词 |
| productKeyEn | 商品属性(英文) | string | 200 | 商品属性英文关键词 |
| productProSet | 商品物流属性(中文) | string[] |  | 商品物流属性中文描述 |
| productProEnSet | 商品物流属性(英文) | string[] |  | 商品物流属性英文描述 |
| productVideo | 商品视频ID列表 | string[] |  | 产品视频URL列表，如果商品包含视频，且features传入enable_video，它将返回值 |
| status | 商品上架状态 | String | 20 | 3表示审核通过 |
| suggestSellPrice | 建议零售价 | String | 200 | unit: $ (USD) |
| listedNum | 刊登数量 | int | 200 | 商品在平台的刊登数量 |
| supplierName | 供应商名称 | string | 200 | 商品供应商名称 |
| supplierId | 供应商id | string | 200 | 商品供应商ID |
| description | 详情 | string | 2000 | 商品详细描述信息 |
| addMarkStatus | 是否包邮? | int | 1 | 0=不包邮, 1=包邮 |
| createTime | 创建时间 | string | 200 | 商品在平台的创建时间 |
| customizationVersion | 定制版本 | int | 20 | 定制商品版本号 |
| customizationJson1 | customization json | string | 200 | 定制信息JSON数据1 |
| customizationJson2 | customization json | string | 200 | 定制信息JSON数据2 |
| customizationJson3 | customization json | string | 200 | 定制信息JSON数据3 |
| customizationJson4 | customization json | string | 200 | 定制信息JSON数据4 |
| variants | 变体列表 | Variant[] | 200 | 商品变体信息列表 |
 variant

 | 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| vid | 变体Id | string | 200 | 商品变体唯一标识符 |
| pid | 商品Id | string | 20 | 所属商品的唯一标识符 |
| variantName | 变体名称 | string | 200 | 变体中文名称 |
| variantNameEn | 变体名称(英文) | string | 200 | 变体英文名称 |
| variantSku | 变体SKU | string | 200 | 变体SKU编码 |
| variantImage | 变体图片 | string | 200 | 变体图片URL |
| variantStandard | 变体规格 | string | 200 | 变体规格描述 |
| variantUnit | 变体单位 | string | 200 | 变体售卖单位 |
| variantProperty | 种类类型 | string | 200 | 变体属性类型 |
| variantKey | 种类关键字 | string | 200 | 变体属性关键词 |
| variantLength | 变体长度 | int | 200 | 单位: mm |
| variantWidth | 变体宽度 | int | 200 | 单位: mm |
| variantHeight | 变体高度 | int | 200 | 单位: mm |
| variantVolume | 变体体积 | int | 200 | 单位: mm3 |
| variantWeight | 变体重量 | double | 200 | 单位: g |
| variantSellPrice | 变体售价 | double | 200 | unit: $ (USD) |
| variantSugSellPrice | 变体建议零售价 | double | 200 | unit: $ (USD) |
| createTime | 创建时间 | string | 200 | 变体创建时间 |
| combineVariants | 子变体列表 | List | 200 | 组合商品的子变体列表 |
| combineNum | 组合子变体数量 | int |  | 组合商品包含的子变体数量 |
 商品类型

 | 商品类型 | 类型意义 | 备注 |
| --- | --- | --- |
| ORDINARY_PRODUCT | 普通商品 |  |
| SERVICE_PRODUCT | 服务商品 |  |
| PACKAGING_PRODUCT | 包装商品 |  |
| SUPPLIER_PRODUCT | 供应商商品 |  |
| SUPPLIER_SHIPPED_PRODUCT | 供应商自发货商品 |  |
 商品状态

 | 商品状态值 | 类型意义 |
| --- | --- |
| 3 | 审核通过 |
 定制版本

 | 定制版本 | 类型意义 |
| --- | --- |
| 0 | 非pod商品 |
| 1 | 平台定制版本V1 |
| 2 | 平台定制版本V2 |
| 3 | 客户定制版本V1 |
| 4 | 客户定制版本V2 |
| 5 | POD3.0平台定制 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  1.4 添加到我的商品 (POST)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/addToMyProduct

 ####  CURL
 ```
curl --location 'http://localhost:8081/api2.0/v1/product/addToMyProduct' \
--header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
--header 'Content-Type: application/json' \
--data '{
    "productId": "1658748072937136128"
}'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| productId | cj商品id | string | 是 | 100 |  |
 ####  Return
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": true,
    "requestId": "a7d4d01b1eed4db9ac2cc1ab7903c98c",
    "success": true
}

```
error

 ```
{
    "code": 1600000,
    "result": false,
    "message": "The product has been added to My Products.",
    "data": null,
    "requestId": "b626475ff68242c3abfea562f9d4f899",
    "success": false
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ##  2 变体
 ###  2.1 查询所有变体(GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/variant/query

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/variant/query?pid=00006BC5-E1F5-4C65-BE2B-3FE0956DA21C' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pid | 商品 id | string | 二选一 | 200 | 查询条件 |
| productSku | 商品 SKU | string | 二选一 | 200 | 查询条件 |
| countryCode | 库存所在国家 | string | 否 | 2 | 如果该参数有值,只会返回在该国家有库存的变体,如果未传值,则不限制库存 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": [
        {
            "vid": "1D72A20A-D113-4FAB-B4BA-6FE1A6A14A3A",
            "pid": "77501FB4-7146-452E-9889-CDF41697E5CF",
            "variantName": null,
            "variantNameEn": "Wwerwieurieowursdklfjskldjfklsdjfksljfklsdjfkldsjfksdjfksljfksdlfsfdfgf XS",
            "variantSku": "CJJSBGBG01517-XS",
            "variantImage": "",
            "variantStandard": "long=5,width=5,height=5",
            "variantUnit": null,
            "variantProperty": null,
            "variantKey": "[\"XS\"]",
            "variantLength": 5,
            "variantWidth": 5,
            "variantHeight": 5,
            "variantVolume": 27,
            "variantWeight": 3.00,
            "variantSellPrice": 3.00,
            "variantSugSellPrice": 3.00,
            "createTime": null
        }
    ],
    "requestId": "00765963-35d0-4a6a-b5cf-aa6731793b10"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| vid | 商品 Id | string | 200 |  |
| pid | 商品名称 | string | 20 |  |
| variantName | 变体名称 | string | 200 |  |
| variantNameEn | 变体名称(英文) | string | 200 |  |
| variantSku | 变体SKU | string | 200 |  |
| variantImage | 变体图片 | string | 200 |  |
| variantStandard | 变体规格 | string | 200 |  |
| variantUnit | 变体单位 | string | 200 |  |
| variantProperty | 种类类型 | string | 200 |  |
| variantKey | 种类关键字 | string | 200 |  |
| variantLength | 变体长度 | int | 200 | 单位: mm |
| variantWidth | 变体宽度 | int | 200 | 单位: mm |
| variantHeight | 变体高度 | int | 200 | 单位: mm |
| variantVolume | 变体体积 | int | 200 | 单位: mm3 |
| variantWeight | 变体重量 | double | 200 | 单位: g |
| variantSellPrice | 变体售价 | double | 200 | unit: $ (USD) |
| variantSugSellPrice | 变体建议零售价 | double | 200 | unit: $ (USD) |
| createTime | 创建时间 | string | 200 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  2.2 变体ID查询(GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/variant/queryByVid

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/variant/queryByVid?vid=1371342252697325568' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| vid | 变体 id | string | 是 | 200 | 查询条件 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": {
        "vid": "1371342252697325568",
        "pid": "00006BC5-E1F5-4C65-BE2B-3FE0956DA21C",
        "variantName": null,
        "variantNameEn": "a-Baby pacifier chain test1 Grey",
        "variantSku": "CJJSBGDY00002-Grey",
        "variantImage": "",
        "variantUnit": null,
        "variantProperty": "[]",
        "variantKey": "Grey",
        "variantLength": 3,
        "variantWidth": 3,
        "variantHeight": 3,
        "variantVolume": 27,
        "variantWeight": 3.00,
        "variantSellPrice": 3.00,
        "createTime": "2021-03-15T14:07:26.000+00:00"
    },
    "requestId": "9b86a5e2-40c3-492c-92b2-4634fa4c4a21"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| vid | 商品 Id | string | 200 |  |
| pid | 商品名称 | string | 20 |  |
| variantName | 变体名称 | string | 200 |  |
| variantNameEn | 变体名称(英文) | string | 200 |  |
| variantSku | 变体SKU | string | 200 |  |
| variantImage | 变体图片 | string | 200 |  |
| variantStandard | 变体规格 | string | 200 |  |
| variantUnit | 变体单位 | string | 200 |  |
| variantProperty | 种类类型 | string | 200 |  |
| variantKey | 种类关键字 | string | 200 |  |
| variantLength | 变体长度 | int | 200 | 单位: mm |
| variantWidth | 变体宽度 | int | 200 | 单位: mm |
| variantHeight | 变体高度 | int | 200 | 单位: mm |
| variantVolume | 变体体积 | int | 200 | 单位: mm3 |
| variantWeight | 变体重量 | double | 200 | 单位: g |
| variantSellPrice | 变体售价 | double | 200 | unit: $ (USD) |
| variantSugSellPrice | 变体建议售价 | double | 200 | unit: $ (USD) |
| createTime | 创建时间 | string | 200 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ##  3 库存
 ###  3.1 查询库存(GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/stock/queryByVid?vid=7874B45D-E971-4DC8-8F59-40530B0F6B77

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/stock/queryByVid?vid=7874B45D-E971-4DC8-8F59-40530B0F6B77' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| vid | 变体 id | string | 是 | 200 | 商品变体唯一标识符 |
 ####  返回
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": [
        {
            "vid": "7874B45D-E971-4DC8-8F59-40530B0F6B77",
            "areaId": "1",
            "areaEn": "China Warehouse",
            "countryCode": "CN",
            "storageNum": 10877
            "totalInventoryNum": 10877
            "cjInventoryNum": 700
            "factoryInventoryNum": 10177
        }...
    ],
    "requestId": "bcde45ac-da31-4fc7-a05e-e3b23a1e6694"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| vid | 变体 Id | string | 200 | 商品变体唯一标识符 |
| areaId | 仓库 Id | bigint | 20 | 仓库区域ID |
| areaEn | 仓库名称 | string | 200 | 仓库区域名称 |
| countryCode | 国家(英文) | string | 200 | 仓库所在国家代码 |
| storageNum | 总库存，请使用totalInventoryNum | int | 20 | 已废弃，请使用totalInventoryNum |
| totalInventoryNum | 总库存 | int | 20 | 当前变体在该仓库的总库存数量 |
| cjInventoryNum | 在CJ仓库管理的库存 | int | 20 | 由CJ直接管理的库存数量 |
| factoryInventoryNum | 在工厂管理的库存 | int | 20 | 由工厂管理的库存数量 |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  |  |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  3.2 按sku查询库存 (GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/stock/queryBySku?sku=CJDS2012593

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/stock/queryBySku?sku=CJDS2012593' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| Parameter | Definition | Type | Required | Length | Note |
| --- | --- | --- | --- | --- | --- |
| sku | SKU 或 SPU | string | Y | 200 |  |
 ####  Return
 success

 ```
{
    "code": 200,
    "result": true,
    "message": "Success",
    "data": [
        {
            "areaEn": "China Warehouse",
            "areaId": 1,
            "countryCode": "CN",
            "totalInventoryNum": 777566,
            "cjInventoryNum": 0,
            "factoryInventoryNum": 777566,
            "countryNameEn": "China"
        },
        {
            "areaEn": "US Warehouse",
            "areaId": 2,
            "countryCode": "US",
            "totalInventoryNum": 36,
            "cjInventoryNum": 36,
            "factoryInventoryNum": 0,
            "countryNameEn": "United States of America (the)"
        }
    ],
    "requestId": "dd4c7d122df24b80a094a4aba073724f",
    "success": true
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| areaId | 仓库 id | int | 20 |  |
| areaEn | 仓库名称 | string | 200 |  |
| countryCode | 国家二字码(EN) | string | 200 |  |
| countryNameEn | 国家名称 | string | 200 |  |
| totalInventoryNum | 总库存 | int | 20 |  |
| cjInventoryNum | 在CJ仓库管理的库存 | int | 20 |  |
| factoryInventoryNum | 在工厂管理的库存 | int | 20 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | error code | int | 20 | [Reference error code](/zh/api/api2/standard/ps-code.html) |
| result | Whether or not the return is normal | boolean | 1 |  |
| message | return message | string | 200 |  |
| data | return data | object |  | interface data return |
| requestId | requestId | string | 48 | Flag request for logging errors |
 ###  3.3 按商品id查询库存 (GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/stock/getInventoryByPid?pid=1444929719182168064

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/stock/getInventoryByPid?pid=1444929719182168064' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| Parameter | Definition | Type | Required | Length | Note |
| --- | --- | --- | --- | --- | --- |
| pid | CJ 商品Id | string | Y | 40 |  |
 ####  Return
 success

 ```
{
    "success": true,
    "code": 200,
    "message": "",
    "data": {
        "inventories": [
            {
                "areaEn": "US Warehouse",
                "areaId": 2,
                "countryCode": "US",
                "totalInventoryNum": 264,
                "cjInventoryNum": 264,
                "factoryInventoryNum": 0,
                "countryNameEn": "US Warehouse"
            }
        ],
        "variantInventories": [
            {
                "vid": "1796078021431009280",
                "inventory": [
                    {
                        "countryCode": "CN",
                        "totalInventory": 10044,
                        "cjInventory": 0,
                        "factoryInventory": 10044,
                        "verifiedWarehouse": 2
                    }
                ]
            }
        ]
    },
    "requestId": "cb927bfa8400421e923a55f81eaafce0"
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | error code | int | 20 | [Reference error code](/zh/api/api2/standard/ps-code.html) |
| result | Whether or not the return is normal | boolean | 1 |  |
| message | return message | string | 200 |  |
| data | Product Inventory Object | object |  |  |
| - inventories | 商品库存列表 | list |  |  |
| -- areaEn | 区域仓名称 | string | 20 | China Warehouse |
| -- areaId | 区域仓id | int | 1 | 1 |
| -- countryCode | 国家二字码 | string | 2 | CN |
| -- totalInventoryNum | 总库存 | int | 20 |  |
| -- cjInventoryNum | 在CJ仓库管理的库存 | int | 20 |  |
| -- factoryInventoryNum | 在工厂管理的库存 | int | 20 |  |
| -- countryNameEn | 国家仓名称 | string | 200 | China Warehouse |
| - variantInventories | 变体库存列表 | list |  |  |
| -- vid | 变体id | string | 20 | China Warehouse |
| -- inventory | 库存集合 | list |  | 1 |
| --- countryCode | 国家二字码 | string | 2 | CN |
| --- totalInventoryNum | 总库存 | int | 20 |  |
| --- cjInventoryNum | 在CJ仓库管理的库存 | int | 20 |  |
| --- factoryInventoryNum | 在工厂管理的库存 | int | 20 |  |
| --- verifiedWarehouse | 验证库存 | int |  | 1: 验证库存 2: 待验证库存 |
| requestId | requestId | string | 48 | Flag request for logging errors |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| Field | Definition | Type | Length | Note |
| --- | --- | --- | --- | --- |
| code | error code | int | 20 | [Reference error code](/zh/api/api2/standard/ps-code.html) |
| result | Whether or not the return is normal | boolean | 1 |  |
| message | return message | string | 200 |  |
| data | return data | object |  | interface data return |
| requestId | requestId | string | 48 | Flag request for logging errors |
 ##  4 评论
 ###  4.1 查询商品评论(GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/comments

 > 将于2024年6月1日弃用, 请使用新接口[查询商品评论](/zh/api/api2/api/product.html#_4-2-查询商品评论-get)

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/comments?pid=7874B45D-E971-4DC8-8F59-40530B0F6B77' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pid | 商品 id | string | 是 | 200 |  |
| score | 评分 | int | 否 | 20 |  |
| pageNum | 页码 | int | 否 | 20 | 默认1 |
| pageSize | 每页纪录数 | int | 否 | 20 | 默认20 |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 0,
    "message": null,
    "data": {
        "pageNum": "1",
        "pageSize": "1",
        "total": "285",
        "list": [
            {
                "commentId": 1536993287524069376,
                "pid": "1534092419615174656",
                "comment": "excelente estado, llegó en una semana, cumple con lo descrito.\nBuena calidad de audio.",
                "commentDate": "2022-06-13T00:00:00+08:00",
                "commentUser": "F***o",
                "score": "5",
                "commentUrls": [
                    "https://cc-west-usa.oss-us-west-1.aliyuncs.com/comment/additional/0001/image/2022-06-15/1126211e-ca15-45ed-95f2-880567ebba37.jpg",
                    "https://cc-west-usa.oss-us-west-1.aliyuncs.com/comment/additional/0001/image/2022-06-15/291ab894-068f-4f4e-b01f-57df72902f58.jpg"
                ],
                "countryCode": "MX",
                "flagIconUrl": "https://cc-west-usa.oss-us-west-1.aliyuncs.com/national-flags/phone/US.png"
            }
        ],
    "requestId": "bcde45ac-da31-4fc7-a05e-e3b23a1e6694"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| commentId | 商品评论ID | int | 20 |  |
| pid | 商品ID | string | 20 |  |
| comment | 商品评论 | string | 200 |  |
| commentDate | 商品评论时间 | String | 50 |  |
| commentUser | 商品评论人 | string | 30 |  |
| score | 商品评论分数 | int | 2 | 长度需要确认一下 |
| commentUrls | 商品评论URL | array |  |  |
| countryCode | 商品评论国家 | string | 10 |  |
| flagIconUrl | 用户国家国旗图标 | string | 200 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  4.2 查询商品评论 (GET)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/productComments

 ####  CURL
 ```
curl --location --request GET 'https://developers.cjdropshipping.com/api2.0/v1/product/productComments?pid=7874B45D-E971-4DC8-8F59-40530B0F6B77' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| pid | 商品 id | string | 是 | 200 |  |
| score | 评分 | int | 否 | 20 |  |
| pageNum | 页码 | int | 否 | 20 | 默认1 |
| pageSize | 每页纪录数 | int | 否 | 20 | 默认20 |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 0,
    "message": null,
    "data": {
        "pageNum": "1",
        "pageSize": "1",
        "total": "285",
        "list": [
            {
                "commentId": 1536993287524069376,
                "pid": "1534092419615174656",
                "comment": "excelente estado, llegó en una semana, cumple con lo descrito.\nBuena calidad de audio.",
                "commentDate": "2022-06-13T00:00:00+08:00",
                "commentUser": "F***o",
                "score": "5",
                "commentUrls": [
                    "https://cc-west-usa.oss-us-west-1.aliyuncs.com/comment/additional/0001/image/2022-06-15/1126211e-ca15-45ed-95f2-880567ebba37.jpg",
                    "https://cc-west-usa.oss-us-west-1.aliyuncs.com/comment/additional/0001/image/2022-06-15/291ab894-068f-4f4e-b01f-57df72902f58.jpg"
                ],
                "countryCode": "MX",
                "flagIconUrl": "https://cc-west-usa.oss-us-west-1.aliyuncs.com/national-flags/phone/US.png"
            }
        ],
    "requestId": "bcde45ac-da31-4fc7-a05e-e3b23a1e6694"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| commentId | 商品评论ID | int | 20 |  |
| pid | 商品ID | string | 20 |  |
| comment | 商品评论 | string | 200 |  |
| commentDate | 商品评论时间 | String | 50 |  |
| commentUser | 商品评论人 | string | 30 |  |
| score | 商品评论分数 | int | 2 | 长度需要确认一下 |
| commentUrls | 商品评论URL | array |  |  |
| countryCode | 商品评论国家 | string | 10 |  |
| flagIconUrl | 用户国家国旗图标 | string | 200 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ##  5 搜品
 ###  5.1 创建搜品 (POST)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/sourcing/create

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/product/sourcing/create' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "thirdProductId": "",
                    "thirdVariantId": "",
                    "thirdProductSku": "",
                    "productName": "",
                    "productImage": "",
                    "productUrl": "",
                    "remark": "",
                    "price": ""
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| thirdProductId | 商品 id | string | 否 | 200 |  |
| thirdVariantId | 变体 id | string | 否 | 200 |  |
| thirdProductSku | 商品 sku | string | 否 | 200 |  |
| productName | 商品名称 | string | 是 | 200 |  |
| productImage | 商品图片 | string | 是 |  |  |
| productUrl | 商品链接 | string | 否 | 200 |  |
| remark | 备注 | string | 否 | 200 |  |
| price | 价格 | double | 否 | 200 | unit: $ (USD) |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 0,
    "message": null,
    "data": {
        "cjSourcingId": "285",
        "result"："success",
     }
    "requestId": "bcde45ac-da31-4fc7-a05e-e3b23a1e6694"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| cjSourcingId | 搜品任务ID | string | 50 |  |
| result | 搜品结果 | String | 20 | success/fail |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |
 ###  5.2 搜品搜索(POST)
 ####  URL
 https://developers.cjdropshipping.com/api2.0/v1/product/sourcing/query

 ####  CURL
 ```
curl --location --request POST 'https://developers.cjdropshipping.com/api2.0/v1/product/sourcing/query' \
                --header 'CJ-Access-Token: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
                --header 'Content-Type: application/json' \
                --data-raw '{
                    "sourceIds": []
                }'

```
| 参数名称 | 参数意义 | 参数类型 | 是否必传 | 长度 | 备注 |
| --- | --- | --- | --- | --- | --- |
| sourceIds | 搜品id集合 | array | 是 | 200 |  |
 ####  返回
 success

 ```
{
    "success": true,
    "code": 0,
    "message": null,
    "data": {
        "sourceId": "285",
        "sourceNumber"："223333",
        "productId": "3324343434",
        "variantId"："4545456",
        "shopId": "285",
        "shopName"："aaaaaaa",
        "sourceStatus": "5",
        "sourceStatusStr"："搜品失败",
        "cjProductId": "285",
        "cjVariantSku"："CJ287690900",
     }
    "requestId": "bcde45ac-da31-4fc7-a05e-e3b23a1e6694"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| sourceId | 搜品id | string | 50 |  |
| sourceNumber | 搜品短码 | String | 50 |  |
| productId | 商品id | String | 50 |  |
| variantId | 变体id | String | 50 |  |
| shopId | 店铺id | String | 50 |  |
| shopName | 店铺名称 | String | 50 |  |
| sourceStatus | 搜品状态 | String | 10 |  |
| sourceStatusStr | 搜品状态  中文 | String | 200 |  |
| cjProductId | cj商品id | String | 50 |  |
| cjVariantSku | cj变体sku | String | 50 |  |
 error

 ```
{
    "code": 1600100,
    "result": false,
    "message": "Param error",
    "data": null,
    "requestId": "323fda9d-3c94-41dc-a944-5cc1b8baf5b1"
}

```
| 返回字段 | 字段意思 | 字段类型 | 长度 | 备注 |
| --- | --- | --- | --- | --- |
| code | 错误码 | int | 20 | [返回错误码标准表](/zh/api/api2/standard/ps-code.html) |
| result | 是否正常返回 | boolean | 1 |  |
| message | 返回信息 | string | 200 |  |
| data |  | Object |  | 接口数据返回 |
| requestId | 请求Id | string | 48 | 用于日志查询错误 |


---

#  附录1：全局错误码
 ##  说明
 每次调用接口时，可能获得正确或错误的返回码，企业可以根据返回码信息调试接口，排查错误。

 注意：开发者的程序应该根据 code 来判断出错的情况，而不应该依赖 message 来匹配，因为 message 可能会调整。
如果请求的参数不符合json规范，可能会导致 CJ 服务器解析到的参数不完整，此时接口在返回的 message 里会有 “The request parameter is not in a correct JSON format”，开发者需要重新检查请求参数的json合法性。 ##  错误码说明
 | 返回码 | 错误说明 | 排查方法 |
| --- | --- | --- |
| 200 | Success | Success |
| 1600000 | System busy, please contact CJ IT | 服务器暂不可用，建议稍候重试。建议重试次数不超过3次。 |
| 1600001 | Invalid API key or access token. How to get access token: https://developers.cjdropshipping.cn/en/api/api2/api/auth.html#_1-1-get-access-token-post | 获取新的Access Token, [查阅文档](/zh/api/api2/api/auth.html#_1-1-get-access-token-post) |
| 1600002 | access token cannot be empty | 传入正确的Access Token |
| 1600003 | Invalid Refresh token | 检查Refresh token或是获取新的Access Token |
| 1600031 | Invalid platform token | 传入正确的platform Access Token |
| 1600030 | token invalidation fail | 获取新的Access Token, [查阅文档](/zh/api/api2/api/auth.html#_1-1-get-access-token-post) |
| 1600004 | Authorization failed, Please check cj account | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1600005 | APIkey is wrong, please check and try again | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1600006 | Developer account not found | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1600007 | The user has been bound to another developer account | 用户已绑定其他开发者账号 |
| 1600008 | Authorization failed, Please check cj account | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1600009 | Token exchange failed because the code does not exist. | 令牌交换失败，因为代码不存在 |
| 1600010 | RedirectUri must be not empty. | RedirectUri 不能为空. |
| 1600011 | CallbackUri must be not empty. | CallbackUri 不能为空. |
| 1600012 | The account creation authorization has been disabled, and cj authorization cannot be created. Contact the CJ account manager. | 帐户创建授权已禁用，无法创建cj授权。联系CJ客户经理。 |
| 1600013 | Store info does not exist,please check and try again. | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1600100 | Interface is offline | 接口已经下线，请检查文档，使用正确的API |
| 1600101 | Interface not found | 接口不正在，请检查文档，使用正确的API |
| 1600200 | Too much request{param} | 调整您的请求速度，以实现更顺畅的分发. 参考：[访问频率限制](/zh/api/api2/standard/limit.html) |
| 1600201 | Quota has been used up | 调整您的请求速度，以实现更顺畅的分发. 参考：[访问频率限制](/zh/api/api2/standard/limit.html) |
| 1600300 | Param error | 检查文档，传入正确的参数. |
| 1600301 | Read timed out | 请求超时，等待一段时间再重试. |
| 1601000 | User not found | 请检查您的电子邮件和API Key是否正确，或者您的API商店是否已授权 |
| 1602000 | Variant not found | 未找到变体，请检查变体ID是否正确 |
| 1602001 | Product not found | 未找到商品，请检查商品ID是否正确 |
| 1602002 | Product has been removed from shelves | 订单支付失败，库存抵扣失败，请联系CJ客服 |
| 1602003 | Variant has been removed from shelves | 变体已经下架 |
| 1602004 | Failed to create infringement report | 创建侵权报告失败 |
| 1603000 | Order create fail | 订单创建失败 |
| 1603001 | Order confirm fail | 订单确认失败 |
| 1603002 | Order delete fail | 订单删除失败 |
| 1603003 | Order exist, please do not duplicate create | 订单号已存在，请勿重复创建 |
| 1603100 | Order not found, please check the CJ order id | 未找到订单，请检查订单id是否正确 |
| 1603101 | Order pay fail, please contact CJ Agent | 订单支付失败，请联系CJ客服 |
| 1603102 | Inventory deduction fail, please contact CJ Agent | 订单支付失败，库存抵扣失败 |
| 1604000 | Balance is insufficient | 余额不足 |
| 1604001 | The balance payment function is temporarily restricted. Please log in to My CJ and make the order payment on the page | 临时限制余额支付功能，请登录My CJ在页面进行订单支付 |
| 1605000 | Logistic not found | 未找到物流 |
| 1605001 | Logistic invalid, please reference freight calculate. | 物流无效，请参考运费计算。 |
| 1605002 | country code not found | 国家码没有发现 |
| 1606000 | Webhook setting add fail, Webhook already have settings | Webhook 设置失败，原因：Webhook 已经设置 |
| 1606001 | You do not meet our service requirements, Please check and try again. 1.Request Protocols: HTTPS, 2. Request Method: POST, 3.Content-Type: application/json, 4. Response Status Code: 200, 5. Response must be returned within 3 seconds. | 调整后再重试 |
| 1607000 | You do not meet our service requirements, Please check and try again. 1.Request Protocols: HTTPS, 2. Request Method: POST, 3.Content-Type: application/json, 4. Response Status Code: 200, 5. Response must be returned within 3 seconds. | 调整后再重试 |
| 1607001 | Please do not use domain names such as localhost, 127.0.0.1 | 调整后再重试 |
| 1607002 | Webhook url error, Please ensure URL starts with https:// | Webhook URL 错误, 请确保URL以https://开头 |
| 1607003 | Webhook url error, Http Status must be 200 | Webhook URL 错误, 请求状态码必须是200 |
| 16070002 | The CJ page type is not supported | CJ跳转页面类型不支持 |
| 1607004 | Freight calculation request failed | 运费运算请求错误 |
| 1607006 | Query dispute product request failed | 纠纷商品查询请求错误 |
| 1607007 | dispute confirm fail | 纠纷确认请求错误 |
| 1607008 | dispute create fail | 纠纷创建失败 |
| 1607009 | dispute cancel fail | 纠纷取消失败 |
| 1607010 | product update fail | 商品更新失败 |
| 16900202 | Request method '{param}' not supported | 检查文档，使用正确的HTTP方法 |
| 16900203 | Content type not supported[{param}] | 检查文档，使用正确的Content-Type |
| 16900204 | Required request body is missing | 检查文档，传入HTTP Body |
| 16900205 | The request parameter is not in a correct JSON format | 检查请求body是不是正确的JSON格式 |
| 16900403 | {param} can not be empty | 检查文档，传入正确的参数 |
 ##  排查方法
 ###  错误码：1600200
 接口调用超过限制。

 - 具体频率策略，参考：[访问频率限制](/zh/api/api2/standard/limit.html)
 - 频率拦截时长一般与调用的限制时长相同，比如说是分钟级别的限制，则在中频率后的1分钟后自动解除。小时、天、以及月份，也是以此类推。
 - 我们对接口调用的频率限制是比较宽松的。对于接口中频率的调用，考虑以下优化：
 - 接口实现时，仅系统失败需要重试。其余错误码，应该排查下调用失败原因
 - 合理调用，对于实时同步数据，可改为准实时，调用是有延迟的，单个用户一天大量的调用，体验是不好的

 ###  错误码：1600300
 传递参数不符合系统要求，需要参照具体API接口说明。同时确认：

 - 1）Http请求方法，是否正确。比如说接口要求以Post方法，就不能使用Get方式
 - 2）Http请求参数，是否正确。比如说，接口内容要求json结构体，就不能以url参数传递或者form-data方式。



---

