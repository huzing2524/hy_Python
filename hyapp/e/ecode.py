SUCCESS = 200
BadRequest = 400
ERROR = 500

LoginFailed = 10000
InvalidParams = 10001
InvalidAccount = 10002
InvalidPassword = 10003
InvalidCode = 10004
WrongCode = 10005
ExistedPhone = 10006
ExistedAccount = 10007
TooManyFails = 10008

DeviceIDExist = 20000

ErrorCode = {
    SUCCESS: "ok",
    ERROR: "fail",
    BadRequest: "请求参数错误！",
    LoginFailed: "错误的用户名或密码！",
    InvalidParams: "输入参数错误！",
    DeviceIDExist: "改设备序列号已添加！",
    InvalidAccount: '账号不存在！',
    ExistedAccount: '账号已存在！',
    ExistedPhone: '手机号已存在！',
    InvalidPassword: '密码错误！',
    InvalidCode: '验证码已失效！',
    WrongCode: '验证码验证失败！',
    TooManyFails: '登录失败次数超过限制！'
}
