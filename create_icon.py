from PIL import Image, ImageDraw

def create_icon():
    # PNG 아이콘 생성 (32x32)
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 원 그리기
    draw.ellipse([2, 2, 30, 30], fill='#2196F3')
    
    # 화살표 그리기
    draw.polygon([(16, 6), (26, 16), (16, 26), (16, 20), (6, 20), (6, 12), (16, 12)], fill='white')
    
    # PNG 저장
    img.save('icon.png')
    
    # ICO 파일 생성 (여러 크기 포함)
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
    icons = []
    
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icons.append(resized)
    
    icons[0].save('icon.ico', format='ICO', sizes=[(i.width, i.height) for i in icons])

if __name__ == '__main__':
    create_icon() 