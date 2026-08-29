---
title: 快速入门Windows Socket编程
date: 2026-08-29
tags: [技术, 介绍]
excerpt: Windows环境下C/C++的socket相关网络编程详解
---

# Windows环境下C/C++的socket相关网络编程

Socket，中文常译为“套接字”。它提供了一种跨网络通信的机制，允许两个不同计算机上的应用程序通过网络进行数据交换。在更具体的层面可以被看作是网络上的两个程序通过一个双向通信链路进行对话的接口。

socket起源于Unix，而Unix/Linux基本哲学之一就是“一切皆文件”，都可以用“打开open –> 读写write/read –> 关闭close”模式来操作。所以有些人也将socket当成是一种特殊的文件，一些socket函数就是对其进行的操作（读/写IO、打开、关闭）。

简单的说，Socket 是一个软件抽象层，它封装了复杂的 TCP/IP 协议族。程序员不需要理解底层网络协议的细节，只需要调用 Socket 提供的 API（如 `connect`， `send`， `receive`， `close`）就能实现网络通信。

------

## 初步实现

我这里先给出服务端和客户端的所有代码，之后我来逐步解释。

#### 服务端

```c++
#include <stdio.h>
#include <string>

#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")

int main() {
    // 初始化申请资源
    WSADATA wsa;
    WSAStartup(MAKEWORD(2,2), &wsa);
    printf("Client starting\n");

    // 创建一个 TCP 套接字。SOCKET 是 Windows 定义的套接字句柄类型
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);

    // 定义一个 sockaddr_in 类型的变量 addr，这个结构体专门用于存储 IP 地址和端口号。
    sockaddr_in addr = {};
    addr.sin_family = AF_INET;   
    addr.sin_port = htons(8888);
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    // 将句柄 s 与指定的本地地址（IP 和端口）绑定起来，并让内核知道要读取多少数据
    bind(s, (sockaddr*)&addr, sizeof(addr));
    printf("Bind success on port 8888\n");

    // 开始监听
    listen(s, 5);
    printf("Listening...\n");

    // 接受客户端连接，第二、三个参数均为 NULL：表示不关心客户端的 IP 和端口信息。
    SOCKET c = accept(s, NULL, NULL);
    printf("Client connected!\n");

    // 从已连接的套接字 c 接收数据，并将接收到的内容存入缓冲区 buf
    std::string receivedmsg = ""; // 用于存储接收到的数据
    char buf[65];     // 分配 64 字节
    while (true) {
        int n = recv(c, buf, sizeof(buf)-1, 0);
        if (n <= 0) break; // 错误处理或连接关闭
        buf[n] = '\0'; // 确保字符串以 null 结尾
        printf("Received %d bytes: %s\n", n, buf);
        receivedmsg.append(buf, n); // 将接收到的数据追加到 msg 中
    }
    printf("Message has been received successfully.\n");
    printf("Total received message: %s\n", receivedmsg.c_str());

    std::string response = "Hello, Client! This is a response message from the server. I received your message successfully. Thank you for connecting!";
    // 发送消息
    int totalSent = 0;
    while (totalSent < response.length()) {
        int sent = send(c, response.c_str() + totalSent, \
                        response.length() - totalSent, 0);
        if (sent == SOCKET_ERROR) break;
        totalSent += sent;
    }
    printf("Message has been sent successfully.\n");

    closesocket(c);
    closesocket(s);
    WSACleanup();
    return 0;
}
```

#### 客户端

```c++
#include <stdio.h>
#include <string>

#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")

int main() {
    // 初始化申请资源
    WSADATA wsa;
    WSAStartup(MAKEWORD(2,2), &wsa);
    printf("Client starting\n");

    // 创建一个 TCP 套接字。SOCKET 是 Windows 定义的套接字句柄类型
    SOCKET s = socket(AF_INET, SOCK_STREAM, 0);

    // 定义一个 sockaddr_in 类型的变量 addr，这个结构体专门用于存储 IP 地址和端口号。
    sockaddr_in addr = {}; 
    addr.sin_family = AF_INET;   
    addr.sin_port = htons(8888);
    addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    connect(s, (sockaddr*)&addr, sizeof(addr));
    printf("Connected to server\n");

    const char* msg = "Hello, Socket Server! This is a test message from the client. I hope you receive it correctly and respond back. Thank you!";
    int totalSent = 0;
    while (totalSent < strlen(msg)) {
        int sent = send(s, msg + totalSent, strlen(msg) - totalSent, 0);
        if (sent == SOCKET_ERROR) break;
        totalSent += sent;
    }
    printf("Message has been sent successfully.\n");
    shutdown(s, SD_SEND); 
    printf("Message sent\n");


    std::string receivedmsg = ""; // 用于存储接收到的数据
    char buf[65];     // 分配 64 字节
    while (true) {
        int n = recv(s, buf, sizeof(buf)-1, 0);
        if (n <= 0) break; // 错误处理或连接关闭
        buf[n] = '\0'; // 确保字符串以 null 结尾
        printf("Received %d bytes: %s\n", n, buf);
        receivedmsg.append(buf, n); // 将接收到的数据追加到 msg 中
    }
    printf("Message has been received successfully.\n");
    printf("Total received message: %s\n", receivedmsg.c_str());


    closesocket(s);
    WSACleanup();
    return 0;
}
```

> 如果你是用VSCode的并且用的不是微软MSVC编译器的，比如用的mingw编译器，由于pragma comment失效，编译链接失败的，在.vscode/tasks.json里的args里加上链接指令 -lws2_32 ，链接一下Winsock的lib库

> 即编译运行  `g++ server.cpp -o server.exe -lws2_32`

#### 代码解释

我的实现简化了许多，类似错误处理的内容都被我删去了，详细可参见[微软的示例代码](https://learn.microsoft.com/zh-cn/windows/win32/winsock/complete-server-code)。

首先是初始化，**WSADATA** 是一个结构体，用于存储 Windows Sockets 实现的详细信息，比如支持的版本号、最大套接字数、供应商信息等。

`MAKEWORD(2,2) `表示请求的 Winsock 版本号为 2.2，`&wsa` 指向 WSADATA 结构体的指针，函数会将实际加载的 Winsock 实现信息填充进去。

> Windows 不像 Linux 那样把网络功能内嵌在系统调用中，而是通过 **动态链接库 ws2_32.dll** 提供网络 API。使用任何网络函数前，必须先通过 `WSAStartup` 告诉系统，并且在程序结束时应调用 `WSACleanup()` 来释放资源。

```c++
// 初始化申请资源
WSADATA wsa;
WSAStartup(MAKEWORD(2,2), &wsa);
```

Winsock 中使用了 `SOCKET` 这一句柄来管理每一个socket（也是应了“一切皆句柄”这句话）。所谓句柄，本质上是一个整数，这样设计就是为了程序不直接碰系统对象本身，而是通过一种不透明的“票据”来间接使用它们，保证了架构的安全。

Winsock 提供的 `socket()` 函数的三个参数如下：

- `af` 地址族：`AF_INET`代表基于 IPv4（IPv6 则用 `AF_INET6`）；
- `type` 套接字类型：`SOCK_STREAM` 套接字类型：面向连接的可靠字节流（即 TCP）。另一种常见的是 `SOCK_DGRAM`（UDP）；
- `protocol` 协议类型。设为 0 表示由系统根据 af 和 type 自动选择。对于 `AF_INET` + `SOCK_STREAM`，自动选 TCP（协议号 6）。

简单来说，这一行的作用就是：**创建一个基于 IPv4 的 TCP 套接字**。

```c++
// 创建一个 TCP 套接字。SOCKET 是 Windows 定义的套接字句柄类型
SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
```

接下来这几行代码是在 **初始化一个 IPv4 地址结构体**，用于指定本机监听的 IP 地址和端口。

```c++
// 定义一个 sockaddr_in 类型的变量 addr，这个结构体专门用于存储 IPv4 地址和端口号。
sockaddr_in addr = {}; // 显式清零是良好的习惯，避免未初始化的垃圾数据引起意外行为。
// 设置地址族为 IPv4，固定为 AF_INET。
addr.sin_family = AF_INET;   
// htons() 函数将 主机字节序（可能是小端）转换为 网络字节序（大端），因为网络协议规定多字节整型使用大端传输
addr.sin_port = htons(8888);
//inet_addr() 函数将点分十进制的字符串转换为 unsigned long 类型的网络字节序二进制值
addr.sin_addr.s_addr = inet_addr("127.0.0.1");
```

服务端这边使用 `bind()` 方法将句柄 s 与指定的本地地址（IP 和端口）绑定起来。

> 这里强制类型转换的原因是：`sockaddr_in` 和 `sockaddr` 的大小相同（16 字节），但前者有明确的字段（family, port, address），后者只是一个通用结构。早期 C 语言没有泛型，所以设计成接受通用指针，由程序员根据 `sa_family` 自行判断真实类型。现在很多新 API 使用 `sockaddr_storage` 作为更大的通用容器，但 `bind` 的接口一直保持这样。

然后开始监听，backlog = 5 表示内核等待连接队列最大长度（即最多允许多少个客户端连接请求排队等候处理）的总容量上限为 5。

接受客户端连接，第二、三个参数均为 NULL表示不关心客户端的 IP 和端口信息。

```c++
// 将句柄 s 与指定的本地地址（IP 和端口）绑定起来，并让内核知道要读取多少数据
bind(s, (sockaddr*)&addr, sizeof(addr));
// 开始监听
listen(s, 5);
// 接受客户端连接
SOCKET c = accept(s, NULL, NULL);
```

客户端这边使用  `connect()` 方法来连接到服务端，用法和 `bind()` 方法基本类似。

```c++
connect(s, (sockaddr*)&addr, sizeof(addr));
```

发送信息

TCP 是流协议，`send` 并不保证一次调用就能发送完所有 `len` 字节。尤其在网络压力大或非阻塞模式下，实际发送的字节数可能小于 `len`。正确的做法是循环发送。

```c++
std::string msg = "This is a test message"
int totalSent = 0;
while (totalSent < msg.length()) {
    int sent = send(c, msg.c_str() + totalSent, msg.length() - totalSent, 0);
    if (sent == SOCKET_ERROR) break;
    totalSent += sent;
}
shutdown(c, SD_SEND); // 半关闭，即关闭发送通道
```

与此类似，接收信息也是采用循环接收。

```c++
std::string receivedmsg = ""; // 用于存储接收到的数据
char buf[65];     // 分配 64 字节
while (true) {
    int n = recv(s, buf, sizeof(buf)-1, 0);
    if (n <= 0) break; // 错误处理或连接关闭
    buf[n] = '\0'; // 确保字符串以 null 结尾，同时防止越界
    printf("Received %d bytes: %s\n", n, buf);
    receivedmsg.append(buf, n); // 将接收到的数据追加到 msg 中
}
```

最后回收资源，防止占用系统资源。

```c++
closesocket(s);
WSACleanup();
```

------

## 结语

感谢你阅读这篇文章！如果你有任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/Ling-Nine/Ling-nine.github.io/issues) 与我交流。

---

*本文使用 Markdown 编写，最后更新于 2026年8月29日*