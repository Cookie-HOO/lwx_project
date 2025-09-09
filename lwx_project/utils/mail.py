import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import os
import mimetypes

from lwx_project.scene.const import AUTH_PATH
from lwx_project.scene.daily_baoxian.const import OLD_RESULT_PATH


def send_mail(from_email, to_email, subject, body, attachments):
    """
    发送邮件，从 AUTH 中获取发件人鉴权信息
    :param from_email: 发件人邮箱
    :param to_email: 收件人邮箱，支持多人，逗号分隔的字符串或list
    :param subject: 邮件主题
    :param body: 邮件正文
    :param attachments: 附件列表
    :return:
    """
    # 读取所有可供鉴权的信息 data/auth.json
    with open(AUTH_PATH) as f:
        AUTH = json.loads(f.read())

    # 获取发件人鉴权信息
    if from_email not in AUTH:
        print(f"未配置发件人邮箱 {from_email} 的鉴权信息")
        return False
    password = AUTH[from_email]
    
    # 创建邮件对象
    msg = MIMEMultipart()
    msg['From'] = from_email
    # 处理收件人
    if isinstance(to_email, list):
        recipients = to_email
    else:
        recipients = to_email.split(',') if ',' in to_email else [to_email]
    # 确保所有收件人都被正确格式化（去除空格）
    recipients = [recipient.strip() for recipient in recipients]
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = Header(subject, 'utf-8')
    
    # 添加正文
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    # 处理附件
    for attachment_path in attachments:
        if not os.path.exists(attachment_path):
            print(f"附件文件不存在: {attachment_path}")
            continue
        
        filename = os.path.basename(attachment_path)
        with open(attachment_path, 'rb') as f:
            # 获取文件MIME类型
            mime_type, _ = mimetypes.guess_type(attachment_path)
            # 手动添加Excel MIME类型映射
            if mime_type is None:
                if attachment_path.endswith('.xlsx'):
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                elif attachment_path.endswith('.xls'):
                    mime_type = 'application/vnd.ms-excel'
                else:
                    mime_type = 'application/octet-stream'
            main_type, sub_type = mime_type.split('/', 1)
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        # 对文件名进行UTF-8编码处理
        encoded_filename = Header(filename, 'utf-8').encode()
        part.add_header('Content-Disposition', 'attachment', filename=encoded_filename)
        msg.attach(part)
    
    # 发送邮件
    try:
        # 根据邮箱域名选择SMTP服务器
        domain = from_email.split('@')[1]
        smtp_config = {
            '126.com': ('smtp.126.com', 465),
            'qq.com': ('smtp.qq.com', 465),
            '163.com': ('smtp.163.com', 465),
            'gmail.com': ('smtp.gmail.com', 587),
            'outlook.com': ('smtp.office365.com', 587)
        }
        
        if domain not in smtp_config:
            print(f"不支持的邮箱域名: {domain}")
            return False
        
        smtp_server, port = smtp_config[domain]
        
        # 连接服务器并发送邮件
        if port == 587:
            server = smtplib.SMTP(smtp_server, port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_server, port)
        
        server.login(from_email, password)
        recipients = to_email.split(',') if ',' in to_email else [to_email]
        server.sendmail(from_email, recipients, msg.as_string())
        server.quit()
        print("邮件发送成功")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False


if __name__ == '__main__':
    send_mail(
        from_email="fy335432620@126.com",
        to_email="fy335432620@126.com",
        subject="python test",
        body="hello",
        attachments=[OLD_RESULT_PATH]
    )