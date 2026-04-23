import argparse
import uvicorn


def run_web(host: str = "0.0.0.0", port: int = 8000, reload: bool = True):
    """启动FastAPI Web服务"""
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


def run_crawler():
    """爬取并写入消息队列"""
    from crawler.genshin.genshin_network import run_crawler as run_genshin_network_crawler
    run_genshin_network_crawler()


def run_worker():
    """启动通用常驻消费者"""
    from worker.run import run_worker as run_queue_worker
    run_queue_worker()


def main():
    """统一入口"""
    parser = argparse.ArgumentParser(description="Nebula Demo")
    parser.add_argument(
        "command",
        choices=["web", "crawler", "worker"],
        help="运行模式: web(启动API服务) / crawler(运行爬虫) / worker(多队列消费并分发)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web服务主机地址")
    parser.add_argument("--port", type=int, default=8000, help="Web服务端口")
    parser.add_argument("--no-reload", action="store_true", help="禁用热重载")

    args = parser.parse_args()

    if args.command == "web":
        run_web(host=args.host, port=args.port, reload=not args.no_reload)
    elif args.command == "crawler":
        run_crawler()
    elif args.command == "worker":
        run_worker()


if __name__ == "__main__":
    main()