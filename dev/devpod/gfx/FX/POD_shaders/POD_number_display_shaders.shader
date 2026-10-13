# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
	"standardfuncsgfx.fxh"
}

VertexShader =
{
	MainCode VS_Default
	{
		Input = "VS_INPUT_PDX_GUI"
		Output = "VS_OUTPUT_PDX_GUI"
		Code
		[[
			PDX_MAIN
			{
				return PdxGuiDefaultVertexShader( Input );
			}
		]]
	}
}

PixelShader =
{
	TextureSampler Texture
	{
		Ref = PdxTexture0
		MagFilter = "Point"
		MinFilter = "Point"
		MipFilter = "Point"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}
	MainCode PS_Default
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			PDX_MAIN
			{
				float4 OutColor = SampleImageSprite( Texture, Input.UV0 );
				OutColor *= Input.Color;
				
				#ifdef DISABLED
					OutColor.rgb = DisableColor( OutColor.rgb );
				#endif
				
			    return OutColor;
			}
		]]
	}
	
	MainCode PS_NUMBERVEINS
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			
			float lineDF(float2 p, float2 a, float2 b)
			{
				float2 pa = p - a;
				float2 ba = b - a;
				float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
				return length(pa - ba * h);
			}

			// numbers from https://www.shadertoy.com/view/4s3XDn
			float _11(float2 uv) {
				return min(min(
						lineDF(uv,float2(-0.2, 0.45),float2(0., 0.6)),
						length(float2(uv.x, max(0.,abs(uv.y-.1)-.5)))),
						length(float2(max(0.,abs(uv.x)-.2), uv.y+.4)));
						
			}
			float _22(float2 uv) {
				float x = min(lineDF(uv,float2(0.185, 0.17),float2(-.25, -.4)),
							length(float2(max(0.,abs(uv.x)-.25), uv.y+.4)));
				uv.y-=.35;
				uv.x += 0.025;
				return min(x,abs(atan2(uv.x, uv.y)-0.63)<1.64?abs(length(uv)-.275):
						length(uv+float2(.23, -.15)));
			}
			float _33(float2 uv) {
				uv.y-=.1;
				uv.y = abs(uv.y);
				uv.y-=.25;
				return atan2(uv.x, uv.y)>-1.?abs(length(uv)-.25):
					min(length(uv+float2(.211, -.134)),length(uv+float2(.0, .25)));
			}
			float _44(float2 uv) {
				float x = min(length(float2(uv.x-.15, max(0.,abs(uv.y-.1)-.5))),
							lineDF(uv,float2(0.15, 0.6),float2(-.25, -.1)));
				return min(x,length(float2(max(0.,abs(uv.x)-.25), uv.y+.1)));
			}
			float _55(float2 uv) {
				float b = min(length(float2(max(0.,abs(uv.x)-.25), uv.y-.6)),
							length(float2(uv.x+.25, max(0.,abs(uv.y-.36)-.236))));
				uv.y += 0.1;
				uv.x += 0.05;
				float c = abs(length(float2(uv.x, max(0.,abs(uv.y)-.0)))-.3);
				return min(b,abs(atan2(uv.x, uv.y)+1.57)<.86 && uv.x<0.?
						length(uv+float2(.2, .224))
						:c);
			}
			float _66(float2 uv) {
				uv.y-=.075;
				uv = -uv;
				float b = abs(length(float2(uv.x, max(0.,abs(uv.y)-.275)))-.25);
				uv.y-=.175;
				float c = abs(length(float2(uv.x, max(0.,abs(uv.y)-.05)))-.25);
				return min(c,cos(atan2(uv.x, uv.y+.45)+0.65)<0.||(uv.x>0.&& uv.y<0.)?b:
						length(uv+float2(0.2, 0.6)));
			}
			//float _77(vec2 uv) {
			//    return min(length(vec2(max(0.,abs(uv.x)-.25),uv.y-.6)),
			//               lineDF(uv,vec2(-0.25,-0.39),vec2(0.25,0.6)));
			//}
			float _77(float2 uv) {
				return min(length(float2(max(0.,abs(uv.x)-.25), uv.y-.6)),
						lineDF(uv,float2(-0.11, -0.39),float2(0.25, 0.6)));
			}
			//float _88(vec2 uv) {
			//    float l = length(vec2(max(0.,abs(uv.x)-.08),uv.y-.1+uv.x*.07));
			//    uv.y-=.1;
			//    uv.y = abs(uv.y);
			//    uv.y-=.245;
			//    return min(abs(length(uv)-.255),l);
			//}
			float _88(float2 uv) {
				float l = length(float2(max(0.,abs(uv.x)-.08), uv.y-.1+uv.x*.07));
				uv.y-=.1;
				uv.y = abs(uv.y);
				uv.y-=.255;
				return min(abs(length(uv)-.255),l);
			}
			float _99(float2 uv) {
				uv.y-=.125;
				float b = abs(length(float2(uv.x, max(0.,abs(uv.y)-.275)))-.25);
				uv.y-=.175;
				float c = abs(length(float2(uv.x, max(0.,abs(uv.y)-.05)))-.25);
				return min(c,cos(atan2(uv.x, uv.y+.45)+0.65)<0.||(uv.x>0.&& uv.y<0.)?b:
						length(uv+float2(0.2, 0.6)));
			}
			float _00(float2 uv) {
				uv.y-=.1;
				return abs(length(float2(uv.x, max(0.,abs(uv.y)-.25)))-.25);
			}

			#define SPACING float2(-0.71, 0.0)

			float getDigitDF(float digit, float2 uv) {
				float dist = 1e6;
				
				if (digit == 0.) { dist = _00(uv); }
				if (digit == 1.) { dist = _11(uv); }
				if (digit == 2.) { dist = _22(uv); }
				if (digit == 3.) { dist = _33(uv); }
				if (digit == 4.) { dist = _44(uv); }
				if (digit == 5.) { dist = _55(uv); }
				if (digit == 6.) { dist = _66(uv); }
				if (digit == 7.) { dist = _77(uv); }
				if (digit == 8.) { dist = _88(uv); }
				if (digit == 9.) { dist = _99(uv); }
				
				return dist;
			}

			//Length of a number in digits
			float numberLength(float n)
			{
				return floor(max(log(n) / log(10.0), 0.0) + 1.0);
			}
			
			// because guess what, the modulo operator works differently in GLSL and HLSL
			// https://stackoverflow.com/questions/7610631/glsl-mod-vs-hlsl-fmod
			float GLSLmod(in float x, in float y) {
				return x - y * floor(x/y);
			}

			// https://www.shadertoy.com/view/4dc3zr
			float getNumDF(float num, in float2 uv) {
				float dist = 1e6;
				float nl = numberLength(num);
				uv -= (nl-1.0)*0.5*SPACING;

				// imagine being good at math and finding out why this doesn't work for 10
				// couldn't be me
				if (num == 10.) {
					dist = min(dist, getDigitDF(1., uv));
					uv += SPACING;
					dist = min(dist, getDigitDF(0., uv));
				}
				else {
					for (float i = nl; i >= 0.0; i--) {
						float digit = floor(GLSLmod(num / pow(10.0,i), 10.0));

						if(num > pow(10.0,i) || i == 0.0)
						{
							dist = min(dist, getDigitDF(digit, uv));
							uv += SPACING;
						}
					}
				}
				
				return dist;
			}

			float getTimeDF(in float2 uv) {
				float time = GuiTime;
				//return getNumDF(10.,uv);
				float df1 = getNumDF(floor(time),uv);
				// float df2 = getNumDF(floor(time)+1.0,uv);
				// float lerpfactor = smoothstep(0.1,0.9,frac(time));
				// return lerp(df1,df2,lerpfactor);
			}

			// veins based on https://www.shadertoy.com/view/M3dXzB
			#define TAO 6.2831853
			#define S smoothstep
			#define SPEED 0.15
			float2 R(float2 u, float a) { return mul(float2x2(cos(a), sin(a), -sin(a), cos(a)), u); }
			float N(float2 uv, float t, float p) {
				float2 a = float2(0., 0.), res = float2(0., 0.);
				float s = 10.;
				for (int j = 0; j < 30; j++) {
					uv = R(uv, 1.);
					a = R(a, 1.);
					float2 L = uv * s + float(j) + a - t;
					a += cos(L);
					res += (.5 + .5 * sin(L)) / s;
					s *= (1.2 - .07 * p);
				}
				return res.x + res.y;
			}

			PDX_MAIN {
				// gui inputs
				float number   = SpriteBorder[0].x; // spriteborder_left   (0)
				float scale    = SpriteBorder[0].y; // spriteborder_top    (0)
				float offset_x = SpriteBorder[0].z; // spriteborder_right  (0)
				float offset_y = SpriteBorder[0].w; // spriteborder_bottom (0)
				
				float3 powcolor1  = SpriteModifyTexturesColors[1].rgb;
				float strength    = SpriteBorder[1].x; // spriteborder_left   (1)
				float screenshake = 1.0 - SpriteTranslateRotateUVAndAlpha[1].w; // alpha (1)
				
				float3 powcolor2  = SpriteModifyTexturesColors[2].rgb;
				
				float3 multcolor = SpriteModifyTexturesColors[3].rgb;
				
				float2 uv = Input.UV0;
				uv.y = 1.0 - uv.y;
				float2 fragCoord = uv * SpriteSize.xy;
				float2 U = fragCoord / SpriteSize.y;
				U.x += 1.0;
				float T = GLSLmod(GuiTime * SPEED * TAO, TAO);
				float H = clamp(.5 * sin(T) * sin(T / 2.) * exp(-T / 4.) + .5, 0., 1.);
				float n = N(U, H * 5., .1) * 1.15;
				
				float2 p = fragCoord.xy / SpriteSize.xy-0.5;
				p.x *= SpriteSize.x/SpriteSize.y;
				scale *= 1.0 + lerp( 0.0, 0.25 * sin(screenshake*PI*2.), screenshake );
				
				float intensity       = S(1., 0., n);
				float intensity_shake = S(0.4, 1., n);
				
				float2 num_offset = float2(offset_x, offset_y);
				
				float df = getNumDF(number, (p+num_offset)*scale);
				
				float df_factor = lerp( abs(0.06-df), max( abs(0.18-df)-0.06, 0.), screenshake);
				float df_intensity = lerp(strength, 0.5, screenshake) * df_factor;
				
				float3 powcolor = lerp(powcolor1, powcolor2, screenshake);
				
				intensity       *= df_intensity;
				intensity_shake *= df_intensity;
				float3 col = powcolor / lerp(intensity, intensity_shake, screenshake);
				
				// GLSL-like tanh
				float3 excol = exp(col*-2.0);
				col = (1.0-excol)/(1.0+excol);
				
				col *= multcolor;
				col -= smoothstep(0.0,-1.0,df);
				
				//float4 tex = SampleImageSprite( Texture, Input.UV0 );
				
				return float4(col, 1.0);
			}
		]]
	}
}

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}

BlendState BlendStateNoAlpha
{
	BlendEnable = no
}

BlendState PreMultipliedAlpha
{
	BlendEnable = yes
	SourceBlend = "ONE"
	DestBlend = "INV_SRC_ALPHA"
}

DepthStencilState DepthStencilState
{
	DepthEnable = no
}

Effect PdxGuiDefault
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
}
Effect PdxGuiDefaultDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	
	Defines = { "DISABLED" }
}

Effect PdxGuiDefaultNoAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = BlendStateNoAlpha
}
Effect PdxGuiDefaultNoAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = BlendStateNoAlpha
	
	Defines = { "DISABLED" }
}

Effect PdxGuiPreMultipliedAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = PreMultipliedAlpha
}
Effect PdxGuiPreMultipliedAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = PreMultipliedAlpha
	
	Defines = { "DISABLED" }
}

Effect PODNumberVeins
{
	VertexShader = "VS_Default"
	PixelShader = "PS_NUMBERVEINS"
}

Effect PODNumberVeinsDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_NUMBERVEINS"
	Defines = { "DISABLED" }
}
