from PIL import Image, ImageDraw, ImageFont
import struct

# Create a colorful cat-themed image
img = Image.new('RGB', (600, 400), color=(30, 30, 50))
draw = ImageDraw.Draw(img)

# Draw a simple cat scene
# Sky gradient effect
for y in range(400):
    r = int(20 + (y/400)*40)
    g = int(20 + (y/400)*30)
    b = int(50 + (y/400)*20)
    draw.line([(0, y), (600, y)], fill=(r, g, b))

# Moon
draw.ellipse([470, 30, 540, 100], fill=(255, 245, 200))
draw.ellipse([490, 25, 555, 90], fill=(30, 35, 60))  # crescent

# Stars
stars = [(50,40),(120,25),(200,60),(300,20),(380,45),(100,80),(450,15),(180,35)]
for sx, sy in stars:
    draw.ellipse([sx-2, sy-2, sx+2, sy+2], fill=(255, 255, 200))

# Ground
draw.rectangle([0, 300, 600, 400], fill=(20, 60, 20))

# Cat body
draw.ellipse([220, 180, 380, 310], fill=(80, 80, 90))
# Cat head
draw.ellipse([240, 110, 360, 210], fill=(80, 80, 90))
# Ears
draw.polygon([(248,130),(228,80),(268,115)], fill=(80,80,90))
draw.polygon([(348,130),(368,80),(330,115)], fill=(80,80,90))
draw.polygon([(250,125),(237,93),(263,113)], fill=(200,120,140))
draw.polygon([(346,125),(359,93),(333,113)], fill=(200,120,140))
# Eyes (glowing)
draw.ellipse([260,145,285,165], fill=(0,220,100))
draw.ellipse([315,145,340,165], fill=(0,220,100))
draw.ellipse([268,150,278,160], fill=(0,0,0))
draw.ellipse([323,150,333,160], fill=(0,0,0))
# Nose
draw.polygon([(295,175),(300,182),(290,182)], fill=(200,100,120))
# Mouth
draw.arc([283,178,297,190], 0, 180, fill=(60,40,50), width=2)
draw.arc([300,178,314,190], 0, 180, fill=(60,40,50), width=2)
# Whiskers
for wy in [172, 178, 184]:
    draw.line([(230, wy), (275, wy+2)], fill=(200,200,200), width=1)
    draw.line([(325, wy+2), (370, wy)], fill=(200,200,200), width=1)
# Tail
draw.arc([340, 260, 460, 340], 180, 360, fill=(80,80,90), width=12)

# Text
draw.text((10, 370), "Can you find what's hidden? 👀", fill=(150,150,180))

img.save('/home/claude/ctf/static/files/cat.jpg', 'JPEG', quality=95)

# Append flag as plaintext bytes (detectable with `strings cat.jpg | grep FLAG`)
with open('/home/claude/ctf/static/files/cat.jpg', 'ab') as f:
    f.write(b'\n<!-- FLAG{steg0_master_101} -->\n')

print("Stego image created: cat.jpg")
print("Test: strings cat.jpg | grep FLAG")
