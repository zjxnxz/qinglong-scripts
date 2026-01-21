/*
 作者：踟蹰
 日期：20260120
 APP：华住会
 功能：签到
 抓包：hweb-personalcenter.huazhu.com/login/autoLogin 此域名下的 user-token （有效期未知，只要手机 app 不退出登录应该就一直有效）
 变量格式：export HZH="自定义账号名称1#xxxxxxxxxxxxx,自定义账号名称2#xxxxxxxxxxxxx" //多个 token 以 , 分隔存储在环境变量中，自定义账号名称与 token 之间用 # 连接
 定时：一天一次
 cron：0 8 * * *
 */
require('dotenv').config(); 

const pushplus_token = process.env.PUSH_PLUS_TOKEN; 
const tokens = process.env.HZH.split(',').map(item => {
    const [name, token] = item.split('#');
    return { name: name.trim(), token: token.trim() };
});
let message = "华住会签到\n\n";

!(async () => {
    if (typeof $request !== "undefined") {
        getToken();
        return;
    }
    for (const { name, token } of tokens) {
        await signin(token, name);
        await status(token, name);
    }
    await notify();
})()
.catch((e) => {
    console.log(`❌失败! 原因: ${e}!`);
})
.finally(() => {
    console.log('结束执行');
});

async function signin(token, name) {
    const signinRequest = {
        url: "https://hweb-mbf.huazhu.com/api/signIn",
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Client-Platform': 'APP-IOS',
            'User-Token': token,
        },
        body: 'state=1&day=' + new Date().getDate() 
    };

    try {
        const data = await post(signinRequest);
        const result = JSON.parse(data);
        if (result?.businessCode === '1000') {
            if (result?.content.success) {
                message += `${name}\n签到:获得积分:${result?.content.point}\n`;
            } else if (result?.content.isSign) {
                message += `${name}\n签到:请勿重复签到\n`;
            }
        } else {
            message += `${name}\n❌${result?.message}\n`;
        }
    } catch (e) {
        message += `${name}\n❌请重新登陆更新Token\n`;
    }
}

async function status(token, name) {
    const statusRequest = {
        url: 'https://hweb-mbf.huazhu.com/api/getPoint',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Client-Platform': 'APP-IOS',
            'User-Token': token,
        },
        body: JSON.stringify({})
    };

    try {
        const data = await post(statusRequest);
        const result = JSON.parse(data);
        if (result?.businessCode === '1000') {
            message += `当前积分:${result?.content.point}\n\n`;
        } else {
            message += `❌请重新登陆更新Token\n\n`;
        }
    } catch (e) {
        message += `${name}\n请求状态失败\n\n`;
    }
}

async function notify() {
    console.log(message);
    await sendPushplusNotification(message);
}

async function sendPushplusNotification(content) {
    const notifyRequest = {
        url: 'https://www.pushplus.plus/send', 
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            token: pushplus_token,
            title: '华住会酒店签到通知', 
            content: content.replace(/\n/g, '<br/>'), 
            template: "html" 
        }),
    };

    try {
        const response = await post(notifyRequest);
        const result = JSON.parse(response);
        if (result.code === 200) {
            console.log('Pushplus通知发送成功');
        } else {
            console.log(`Pushplus通知发送失败: ${result.msg}`);
        }
    } catch (error) {
        console.log('❌发送Pushplus通知时出错:', error);
    }
}

function post(request) {
    return new Promise((resolve, reject) => {
        const fetch = require('node-fetch');
        fetch(request.url, {
            method: request.method || 'POST',
            headers: request.headers,
            body: request.body || undefined, 
        })
        .then(response => response.text())
        .then(data => resolve(data))
        .catch(error => reject(error));
    });
}
