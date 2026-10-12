from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import qrcode, json, argparse
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description='Tarjeta de cierre de Línea de pase')
p.add_argument('--output', required=True)
p.add_argument('--font', default='DejaVuSans.ttf')
p.add_argument('--font-bold', default='DejaVuSans-Bold.ttf')
args=p.parse_args()
identidad=json.loads((ROOT/'contenidos/identidad.json').read_text())
W=Path(args.output).parent
W.mkdir(parents=True,exist_ok=True)
BG=(7,23,34); MINT='#83dbc0';WHITE='#eef5fa';GRAY='#b2c6d1'
def font(n,b=False):return ImageFont.truetype(args.font_bold if b else args.font,n)
logo=Image.open(ROOT/'assets/logo.png').convert('RGBA')

card=Image.new('RGB',(1920,1080),BG);d=ImageDraw.Draw(card)
# Líneas de campo discretas, continuando la estética del vídeo.
for x in range(-360,2200,270):d.line((x,1080,x+330,0),fill=(14,35,47),width=2)
l=logo.copy();l.thumbnail((132,99));card.paste(l,(590,105),l)
d.text((745,108),'Línea de pase',font=font(60,True),fill=MINT)
name=identidad['autor'];d.text(((1920-d.textlength(name,font=font(34)))/2,245),name,font=font(34),fill=WHITE)
d.line((180,345,1740,345),fill=(54,80,94),width=2)
d.text((180,411),'Más análisis de fútbol en',font=font(34),fill=GRAY)
d.text((180,468),identidad['web'].removeprefix('https://').rstrip('/'),font=font(54,True),fill=WHITE)
d.text((180,599),'También en LinkedIn',font=font(32),fill=MINT)
d.text((180,649),name,font=font(32),fill=WHITE)
url=identidad['linkedin']
qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=7,border=4);qr.add_data(url);qr.make(fit=True)
qi=qr.make_image(fill_color=BG,back_color='white').convert('RGB');qi=qi.resize((300,300),Image.Resampling.NEAREST)
card.paste(qi,(1435,408));d.text((1455,735),'Mi perfil de LinkedIn',font=font(22),fill=WHITE)
d.text((180,805),'Fuentes del vídeo: Opta / FotMob · Hudl Statsbomb (concepto del xG)',font=font(23),fill=GRAY)
d.text((180,862),'Música: Carefree — Kevin MacLeod (incompetech.com)',font=font(23),fill=GRAY)
d.text((180,904),'CC BY 4.0 · creativecommons.org/licenses/by/4.0/ · Recorte y mezcla',font=font(22),fill=GRAY)
card.save(args.output)
