consumer_key = '3KLfDK7RR9DNfN4u_DSiybf2Mnoa'
secretKey = 'G17tqyYCbrNaPQ6EmYNAg_4TMhka'
login_password = 'P@ssword1234'
mobileNumber = '+919898989819'
MPIN = '123456'
access_token = 'eyJ4NXQiOiJNbUprWWpVMlpETmpNelpqTURBM05UZ3pObUUxTm1NNU1qTXpNR1kyWm1OaFpHUTFNakE1TmciLCJraWQiOiJaalJqTUdRek9URmhPV1EwTm1WallXWTNZemRtWkdOa1pUUmpaVEUxTlRnMFkyWTBZVEUyTlRCaVlURTRNak5tWkRVeE5qZ3pPVGM0TWpGbFkyWXpOUV9SUzI1NiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJVQVQwMTUiLCJhdXQiOiJBUFBMSUNBVElPTiIsImF1ZCI6IjNLTGZESzdSUjlETmZONHVfRFNpeWJmMk1ub2EiLCJuYmYiOjE3MDYyNjQwMDksImF6cCI6IjNLTGZESzdSUjlETmZONHVfRFNpeWJmMk1ub2EiLCJzY29wZSI6ImRlZmF1bHQiLCJpc3MiOiJodHRwczpcL1wvYXBpbS5rb3Rha3NlY3VyaXRpZXMub25saW5lOjQ0M1wvb2F1dGgyXC90b2tlbiIsImV4cCI6MzYwMDAwMTcwNjI2NDAwOSwiaWF0IjoxNzA2MjY0MDA5LCJqdGkiOiIyMWQxNmE4Zi1hZDBlLTQ1OWYtOTUzZi1lODgwMDdlNjJjZGYifQ.DSjuoNDCQwcf2lsdDZd2lqTsNbkbFSpVqzsbr5TeS-aiizxPMF4ddktDWZxK6gwnYwkt0kgJtCYObr6vrbtZuoAHtGvTDfslHP6eVJxARh0tiAvF_ZFuLBUnrfGhOXZVHsvxUBu3g0nZZqJ1w5EB-JRB5Pn2qu22LLboG-CAUZHdEcEA55xFjWEcOYUinNtebrWa_nsbRolU9wgcZi6G5sIpcv4CDlotOHqLdpoSvb_9l8tliR8BxfAoCIjvR5hyOwuUsALdoIrHnl-DPQ0-FUBP_fgkT6GiaH6v8i7m4bwc848f1vi3CSMYvcsWaHtqgpdBpqSP0OiNhL-YI9KwSQ'


# secretKey = 'kXb9SoaGI7hfGu58GmvDhhrWxuUa'
# consumer_key = 'cus86mW4sL74SQcbWxrE9xJ9O9sa'
# login_password = 'Naina@7557'
# mobileNumber = '+917348393452'
# MPIN = '991975'


import pyotp
#credentials
finvasia = {"user"    : "FA210129",
"pwd"     : "Naina@7557",
"factor2" : pyotp.TOTP('GEW23NK4264EK7355J33UAPH26WSL2W5').now(),
"vc"      : "FA210129_U",
"app_key" : "c84f66d45ab96529437cee4b22ef7e47",
"imei"    : "abc1234",
}

#kotak
kotak = {
    "consumer_key" : '3KLfDK7RR9DNfN4u_DSiybf2Mnoa',
    'secretKey' : 'G17tqyYCbrNaPQ6EmYNAg_4TMhka',
    'login_password' : 'P@ssword1234',
    'mobileNumber' : '+919898989819',
    'MPIN' : '123456',
    'access_token' : 'eyJ4NXQiOiJNbUprWWpVMlpETmpNelpqTURBM05UZ3pObUUxTm1NNU1qTXpNR1kyWm1OaFpHUTFNakE1TmciLCJraWQiOiJaalJqTUdRek9URmhPV1EwTm1WallXWTNZemRtWkdOa1pUUmpaVEUxTlRnMFkyWTBZVEUyTlRCaVlURTRNak5tWkRVeE5qZ3pPVGM0TWpGbFkyWXpOUV9SUzI1NiIsImFsZyI6IlJTMjU2In0.eyJzdWIiOiJVQVQwMTUiLCJhdXQiOiJBUFBMSUNBVElPTiIsImF1ZCI6IjNLTGZESzdSUjlETmZONHVfRFNpeWJmMk1ub2EiLCJuYmYiOjE3MTAxNTI2NzYsImF6cCI6IjNLTGZESzdSUjlETmZONHVfRFNpeWJmMk1ub2EiLCJzY29wZSI6ImRlZmF1bHQiLCJpc3MiOiJodHRwczpcL1wvYXBpbS5rb3Rha3NlY3VyaXRpZXMub25saW5lOjQ0M1wvb2F1dGgyXC90b2tlbiIsImV4cCI6MzYwMDAwMTcxMDE1MjY3NiwiaWF0IjoxNzEwMTUyNjc2LCJqdGkiOiI0OTNhM2YwZi0wZjMxLTQ2N2UtODgyNC00ZDRjZmZmZjIwZTAifQ.GB38Nio9b0Mv3f4NFy4hENxeSxFhVvMyaA83qynFSxxaSAqfLmcQg7cBhO4xkLtzP8qJ7HIiMfscATSUkKdTBwmFtUXarSWbWDEDuPjeWo_Q61qqbCsrQxWmChLi32qjSC3bOviMAvhRRPjFEGrt90QL8fKIke-h-zxiUzyUs32uEcTKhvqCuajGSCOP2x2mbmjJf_wx2QxWXfb5jrXZN74IBoBDymz58axQNArfimo2XiGP685ztS0yhUzP-457SZwMdzN8O1tcimlOZs0_mld2i-c0yhn_RjzLFFw6C86KPDcjYrRpzFlXZsEIzTlwW4J3_aaIMqRtRgW5qkoXeg'
}