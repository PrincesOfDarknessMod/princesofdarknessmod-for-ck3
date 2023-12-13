# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
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
	MainCode PS_Unmoored
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/ldBSRd

			float2 random2(float2 c) { float j = 4906.0*sin(dot(c,float2(169.7, 5.8))); float2 r; r.x = frac(512.0*j); j *= .125; r.y = frac(512.0*j);return r-0.5;}

			static const float F2 =  0.3660254;
			static const float G2 = -0.2113249;

			float simplex2d(float2 p){float2 s = floor(p + (p.x+p.y)*F2),x = p - s - (s.x+s.y)*G2; float e = step(0.0, x.x-x.y); float2 i1 = float2(e, 1.0-e),  x1 = x - i1 - G2, x2 = x - 1.0 - 2.0*G2; float3 w, d; w.x = dot(x, x); w.y = dot(x1, x1); w.z = dot(x2, x2); w = max(0.5 - w, 0.0); d.x = dot(random2(s + 0.0), x); d.y = dot(random2(s +  i1), x1); d.z = dot(random2(s + 1.0), x2); w *= w; w *= w; d *= w; return dot(d, float3(70.0,70.0,70.0));}

			float3 rgb2yiq(float3 color){return mul( color, float3x3(0.299,0.587,0.114,0.596,-0.274,-0.321,0.211,-0.523,0.311) );}
			float3 yiq2rgb(float3 color){return mul( color, float3x3(1.,0.956,0.621,1,-0.272,-0.647,1.,-1.107,1.705) );}

			float3 convertRGB443quant(float3 color){ float3 out0 = mod(color,1./16.); out0.b = mod(color.b, 1./8.); return out0;}
			float3 convertRGB443(float3 color){return color-convertRGB443quant(color);}

			float2 sincos( float x ){return float2(sin(x), cos(x));}
			float2 rotate2d(float2 uv, float phi){float2 t = sincos(phi); return float2(uv.x*t.y-uv.y*t.x, uv.x*t.x+uv.y*t.y);}
			float3 rotate3d(float3 p, float3 v, float phi){ v = normalize(v); float2 t = sincos(-phi); float s = t.x, c = t.y, x =-v.x, y =-v.y, z =-v.z; float4x4 M = float4x4(x*x*(1.-c)+c,x*y*(1.-c)-z*s,x*z*(1.-c)+y*s,0.,y*x*(1.-c)+z*s,y*y*(1.-c)+c,y*z*(1.-c)-x*s,0.,z*x*(1.-c)-y*s,z*y*(1.-c)+x*s,z*z*(1.-c)+c,0.,0.,0.,0.,1.);return (mul(float4(p,1.),M)).xyz;}

			float varazslat(float2 position, float time){
				float color = 0.0;
				float t = 2.*time;
				color += sin(position.x*cos(t/10.0)*20.0 )+cos(position.x*cos(t/15.)*10.0 );
				color += sin(position.y*sin(t/ 5.0)*15.0 )+cos(position.x*sin(t/25.)*20.0 );
				color += sin(position.x*sin(t/10.0)*  .2 )+sin(position.y*sin(t/35.)*10.);
				color *= sin(t/10.)*.5;
				
				return color;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				float time = GlobalTime * 1.1;
				uv = (uv-.5)*3.;
				
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv.x *= TextureSize.x / TextureSize.y;
			
				float3 vlsd = float3(0,1,0);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				
				float2 
					v0 = .75 * sincos(.3457 * time + .3423) - simplex2d(uv * .917),
					v1 = .75 * sincos(.7435 * time + .4565) - simplex2d(uv * .521), 
					v2 = .75 * sincos(.5345 * time + .3434) - simplex2d(uv * .759);
				
				float3 color = float3(dot(uv-v0, vlsd.xy),dot(uv-v1, vlsd.yz),dot(uv-v2, vlsd.zx));
				
				color *= .2 + 2.5*float3(
					(16.*simplex2d(uv+v0) + 8.*simplex2d((uv+v0)*2.) + 4.*simplex2d((uv+v0)*4.) + 2.*simplex2d((uv+v0)*8.) + simplex2d((v0+uv)*16.))/32.,
					(16.*simplex2d(uv+v1) + 8.*simplex2d((uv+v1)*2.) + 4.*simplex2d((uv+v1)*4.) + 2.*simplex2d((uv+v1)*8.) + simplex2d((v1+uv)*16.))/32.,
					(16.*simplex2d(uv+v2) + 8.*simplex2d((uv+v2)*2.) + 4.*simplex2d((uv+v2)*4.) + 2.*simplex2d((uv+v2)*8.) + simplex2d((v2+uv)*16.))/32.
				);
				
				color = yiq2rgb(color);
				
				color *= 1.- .25* float3(
					varazslat(uv *.25, time + .5),
					varazslat(uv * .7, time + .2),
					varazslat(uv * .4, time + .7)
				);
				
				color = float3(0.1 + (color.r * 0.9), 0.15, color.b);
				
				// background blend
				//float background = 1. * smoothstep(1.0,0.,length(uv));
				//background = 1. - background;
				//color.b = lerp(color.b, background, 0.2);

				color = float3(pow(color.r, 0.4), color.g, pow(color.b, 0.4));

				return float4(color, SampleImageSprite(Texture,Input.UV0).a);
			}
		]]
	}
	MainCode PS_Kaleidoscope
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/WsSGWG

			float2x2 rot(float x)
			{
				return float2x2(cos(x), sin(x), -sin(x), cos(x));
			}

			float2 foldRotate(in float2 p, in float s) {
				//float a = PI / s - atan(p.x, p.y);
				float a = PI / s - atan2(p.y, p.x);
				float n = PI * 2. / s;
				a = floor(a / n) * n;
				p = mul(p, rot(a));
				return p;
			}

			float sdRect( float2 p, float2 b )
			{
				float2 d = abs(p) - b;
				return min(max(d.x, d.y),0.0) + length(max(d,0.0));
			}

			// TheGrid by dila
			// https://www.shadertoy.com/view/llcXWr
			float tex(float2 p, float z)
			{
				p = foldRotate(p, 8.0);
				float2 q = (frac(p / 10.0) - 0.5) * 10.0;
				for (int i = 0; i < 3; ++i) {
					for(int j = 0; j < 2; j++) {
						q = abs(q) - .25;
						q = mul(q, rot(PI * .25));
					}
					q = abs(q) - float2(1.0, 1.5);
					q = mul(q, rot(PI * .25 * z));
					q = foldRotate(q, 3.0);  
				}
				float d = sdRect(q, float2(1., 1.));
				float f = 1.0 / (1.0 + abs(d));
				return smoothstep(.9, 1., f);
			}

			// The Drive Home by BigWings
			// https://www.shadertoy.com/view/MdfBRX
			float Bokeh(float2 p, float2 sp, float size, float mi, float blur)
			{
				float d = length(p - sp);
				float c = smoothstep(size, size*(1.-blur), d);
				c *= lerp(mi, 1., smoothstep(size*.8, size, d));
				return c;
			}

			float2 hash( float2 p ){
				p = float2( dot(p,float2(127.1,311.7)),dot(p,float2(269.5,183.3)));
				return frac(sin(p)*43758.5453) * 2.0 - 1.0;
			}

			float dirt(float2 uv, float n)
			{
				float2 p = frac(uv * n);
				float2 st = (floor(uv * n) + 0.5) / n;
				float2 rnd = hash(st);
				return Bokeh(p, float2(0.5, 0.5) + float2(0.2,0.2) * rnd, 0.05, abs(rnd.y * 0.4) + 0.3, 0.25 + rnd.x * rnd.y * 0.2);
			}

			float sm(float start, float end, float t, float smo)
			{
				return smoothstep(start, start + smo, t) - smoothstep(end - smo, end, t);
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				uv = uv * 2.0 - 1.0;
				
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv.x *= TextureSize.x / TextureSize.y * 1.4;
				uv.x -= 0.8;
				uv *= 2.0;
				
				float3 col = float3(0.0, 0.0, 0.0);
				#define N 3
				#define NN float(N)
				#define INTERVAL 6.0
				#define INTENSITY1 (NN * INTERVAL - t) / (NN * INTERVAL)
				#define INTENSITY float3(INTENSITY1, INTENSITY1, INTENSITY1)
				
				float time = GlobalTime * 0.4;

				for(int i = 0; i < N; i++) {
					float t;
					float ii = float(N - i);
					t = ii * INTERVAL - mod(time - INTERVAL * 0.75, INTERVAL);
					col = lerp(col, INTENSITY, dirt(mod(uv * max(0.0, t) * 0.1 + float2(.2, -.2) * time, 1.2), 3.5));
					
					t = ii * INTERVAL - mod(time + INTERVAL * 0.5, INTERVAL);
					col = lerp(col, INTENSITY * float3(0.7, 0.8, 1.0) * 1.3,tex(uv * max(0.0, t), 4.45));
					
					t = ii * INTERVAL - mod(time - INTERVAL * 0.25, INTERVAL);
					col = lerp(col, INTENSITY * float3(1.,1.,1.), dirt(mod(uv * max(0.0, t) * 0.1 + float2(-.2, -.2) *  time, 1.2), 3.5));
					
					t = ii * INTERVAL - mod(time, INTERVAL);
					float r = length(uv * 2.0 * max(0.0, t));
					float rr = sm(-24.0, -0.0, (r - mod(time * 30.0, 90.0)), 10.0);
					col = lerp(col, lerp(INTENSITY * float3(1.,1.,1.), INTENSITY * float3(0.7, 0.5, 1.0) * 3.0, rr),tex(uv * 2.0 * max(0.0, t), 0.27 + (2.0 * rr)));

				}

				col = float3( col.r * 0.9, 0.12, col.b * 0.3 );
				
				return float4(col, SampleImageSprite(Texture,Input.UV0).a);
			}
		]]
	}
}

# SampleImageSprite( Texture, Input.UV0 );

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

Effect Unmoored
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Unmoored"
}
Effect UnmooredDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Unmoored"
	
	Defines = { "DISABLED" }
}

Effect Kaleidoscope
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Kaleidoscope"
}
Effect KaleidoscopeDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Kaleidoscope"
	
	Defines = { "DISABLED" }
}