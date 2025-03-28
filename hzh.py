/*
 作者：踟蹰
 日期：20241024
 APP：华住会
 功能：签到
 抓包：hweb-personalcenter.huazhu.com/login/autoLogin 此域名下的 user-token （有效期未知）
 变量格式：export HZH_Token="xxxxxxxxxxxxx,xxxxxxxxxxxxx" //多个 token 以逗号分隔存储在环境变量中
 定时：一天一次
 cron：0 8 * * *
 */
require('dotenv').config(); 

const pushplus_token = process.env.PUSH_PLUS_TOKEN; 
const tokens = process.env.HZH_Token.split(',');
let message = "华住会签到\n";

!(async () => {
    if (typeof $request !== "undefined") {
        getToken();
        return;
    }
    for (const token of tokens) {
        await signin(token);
        await status(token);
    }
    await notify();
})()
.catch((e) => {
    console.log(`❌失败! 原因: ${e}!`);
})
.finally(() => {
    console.log('结束执行');
});

async function signin(token) {
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
                message += `Token: ${token} 签到:获得积分:${result?.content.point}\n`;
            } else if (result?.content.isSign) {
                message += `Token: ${token} 签到:请勿重复签到\n`;
            }
        } else {
            message += `Token: ${token} ❌${result?.message}\n`;
        }
    } catch (e) {
        console.log(`Token: ${token} ❌请重新登陆更新Token`);
    }
}

async function status(token) {
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
            message += `Token: ${token} 当前积分:${result?.content.point}\n`;
        } else {
            console.log(`Token: ${token} ❌请重新登陆更新Token`);
        }
    } catch (e) {
        console.log(`Token: ${token} 请求状态失败:`, e);
    }
}

async function notify() {
    console.log(message);
    await sendPushplusNotification(message);
}

async function sendPushplusNotification(content) {
    const notifyRequest = {
        url: 'http://www.pushplus.plus/send',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            token: pushplus_token,
            title: '华住会酒店签到通知', 
            content: content,
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
