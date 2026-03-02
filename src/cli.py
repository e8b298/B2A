import argparse

def main():
    parser = argparse.ArgumentParser(description="Bilibili Hybrid Extractor - 文本与视觉多模态视频内容提取工具")
    parser.add_argument("url", help="B站视频URL或BV号")
    parser.add_argument("--visual", action="store_true", help="启用深度视觉提取（抽取视频关键帧）")
    args = parser.parse_args()
    print(f"Target: {args.url}, Visual Mode: {args.visual}")

if __name__ == "__main__":
    main()
