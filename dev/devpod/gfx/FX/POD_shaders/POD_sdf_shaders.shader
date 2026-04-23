# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
	"cw/pdxgui_sprite_textures.fxh"
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

	MainCode PS_PODSDF_LOADINGSCREEN
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			#define TAU    (2.0*PI)
			#define TIME   (GuiTime+120.0)
			#define TTIME  (TIME*TAU)
			#define PERIOD 600.0

			#define SDF_SIZE 512.0f

			static const float2x2 frot = float2x2(0.80, 0.60, -0.60, 0.80);

			void rot(inout float2 p, float a) {
				float c = cos(a);
				float s = sin(a);
				p = float2(c*p.x + s*p.y, -s*p.x + c*p.y);
			}

			float noise(float2 p) {
				float a = sin(p.x);
				float b = sin(p.y);
				float c = 0.5 + 0.5*cos(p.x + p.y);
				float d = lerp(a, b, c);
				return d;
			}

			float fbm(float2 p) {    
				float f = 0.0;
				float a = 1.0;
				float s = 0.0;
				float m = 2.0-0.1;
				for (int x = 0; x < 4; ++x) {
					f += a*noise(p);
					p = mul(frot,p) * m;
					m += 0.01;
					s += a;
					a *= 0.45;
				}
				return f/s;
			}

			float warp(float2 p, float offset, out float2 v, out float2 w) {
				float2 vx = float2(0.0, 0.0);
				float2 vy = float2(3.2, 1.3);

				float2 wx = float2(1.7, 9.2);
				float2 wy = float2(8.3, 2.8);

				float2 off = (1.75 + 0.5*cos(TTIME/60.0))*float2(-5, 5);

				p += lerp(float2(0.0,0.0), off, 0.5 + 0.5*tanh(offset));

				rot(vx, TTIME/1000.0);
				rot(vy, TTIME/900.0);

				rot(wx, TTIME/800.0);
				rot(wy, TTIME/700.0);

				float2 vv = float2(fbm(p + vx), fbm(p + vy));  
				float2 ww = float2(fbm(p + 3.0*vv + wx), fbm(p + 3.0*vv + wy));

				float f = fbm(p + 2.25*ww);


				v = vv;
				w = ww;

				//  return tanh(f);
				return f;
			}

			float pmin(float a, float b, float k) {
				float h = max(k-abs(a-b), 0.0)/k;
				return min(a, b) - h*h*k*(1.0/4.0);
			}
			
			float get_texture_sdf(PdxTextureSampler2D Texture, float2 uv) {
				float sdf = PdxTex2D(Texture, uv).r;
				if ( uv.x < 0. || uv.x > 1. || uv.y < 0. || uv.y > 1. ) {
					return 0.;
				}
				else {
					return sdf;
				}
			}

			float df(float2 uv, float2 texSize) {
				float2 sdf1_offset = SpriteBorder[1].xy;
				float2 sdf2_offset = SpriteBorder[2].xy;
				
				float sdf1_scale = SpriteTranslateRotateUVAndAlpha[1].z;
				float sdf2_scale = SpriteTranslateRotateUVAndAlpha[2].z;
				
				//float2 sdf_uv = ( p + float2(.5,.5) ) * 1.25;
				float2 sdf1_uv = ( uv - sdf1_offset ) * texSize / SDF_SIZE * sdf1_scale;
				float2 sdf2_uv = ( uv - sdf2_offset ) * texSize / SDF_SIZE * sdf2_scale;
				float sdf1 = get_texture_sdf(ModifyTexture0, sdf1_uv);
				float sdf2 = get_texture_sdf(ModifyTexture1, sdf2_uv);

				float sdflerp = cos(GuiTime * 0.2) * .5 + .5;
				float lerped_sdf = lerp(sdf1, sdf2, sdflerp);

				return 0.5 - lerped_sdf;
			}

			float3 normal(float2 p, float offset) {
				float2 v;
				float2 w;
				float2 e = float2(0.0001, 0);
				
				float3 n;
				n.x = warp(p + e.xy, offset, v, w) - warp(p - e.xy, offset, v, w);
				n.y = 2.0*e.x;
				n.z = warp(p + e.yx, offset, v, w) - warp(p - e.yx, offset, v, w);
				
				return normalize(n);
			}


			float3 postProcess(float3 col) {
				col=pow(clamp(col,0.0,1.0),float3(0.75,0.75,0.75));
				col=col*0.6+0.4*col*col*(3.0-2.0*col);  // contrast
				float saturator = dot(col, float3(0.33,0.33,0.33));
				col=lerp(col, float3(saturator,saturator,saturator), -0.4);  // saturation
				return col;
			}

			PDX_MAIN {
				float2 TextureSize = SpriteSize.xy;

				float2 uv = Input.UV0;
				uv.x = 1.0 - uv.x;
				uv.x *= TextureSize.x / TextureSize.y;

				float2 p = 2. * uv - float2(1.,1.);

				p *= 2.0;
				float3 col = float3(1.0,1.0,1.0);
				
				float d = df(Input.UV0,TextureSize);
				p += -0.025*TTIME*float2(-1.0, 1.0);
				
				float2 v;
				float2 w;
				
				float f = warp(p, d, v, w);
				float3 n = normal(p, d);

				float3 lig = normalize(float3(0.6, -0.4, -0.4));
				//  rot(lig.xz, TTIME/100.0);
				float dif = max(dot(lig, n), 0.5);

				//const float3 col1 = float3(0.3, 0.2, 0.2);
				//const float3 col2 = float3(0.2, 0.5, 0.6);
				const float3 col1 = float3(0.2, 0.2, 0.2);
				const float3 col2 = float3(0.1, 0.3, 0.8);
				
				float c1 = dot(normalize(lig.xz), v)/length(v);
				float c2 = dot(normalize(lig.xz), w)/length(w);
				
				col = pow(dif, 0.75)*tanh(pow(abs(f + 0.5), 1.5)) + c1*col1 + c2*col2;
				//col += 0.4*float3(smoothstep(0.0, -0.0125, d));
				float outline = smoothstep(0.0, -0.01, d*0.5);
  				col += 0.6*float3(outline,outline,outline);

				//col = postProcess(col);

				//col *= smoothstep(0.0, 16.0, GuiTime*GuiTime);
				
				float expR = SpriteBorder[3].x;
				float expG = SpriteBorder[3].y;
				float expB = SpriteBorder[3].z;

				//col = float3(col.r, 0.0, col.r*col.r*col.r*col.r*col.r*0.25); // default (red)
				col = float3( pow(col.r,expR), pow(col.r,expG), pow(col.r,expB) ) * SpriteModifyTexturesColors[3].xyz;
				col = clamp(col,float3(0.,0.,0.),float3(1.,1.,1.));
				float colMax = max(max(col.r,col.g),col.b);

				//float alpha = 1.0 - ( (1.0 - col.r) * (1.0 - SampleImageSprite(Texture,Input.UV0).a) );
				float alpha = SampleImageSprite(Texture,Input.UV0).a * lerp(colMax, 1.0, SpriteBorder[0].x);

				//float alpha = 1.0;

				// if (uv.y >= 0.91 || uv.y <= 0.09) {
				// 	alpha = 0.0;
				// }

				return float4(col, alpha);
			}
		]]
	}

	MainCode PS_PODSDF_LOADINGSCREEN2
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// based on https://www.shadertoy.com/view/3t2czh
			
			// Licence CC0: Liquid Metal
			// Some experimenting with warped FBM and very very fake lighting turned out ok 
			
			//#define PI  3.141592654
			#define TAU (2.0*PI)

			#define SDF_SIZE 512.0f

			void rot(inout float2 p, float a) {
				float c = cos(a);
				float s = sin(a);
				p = float2(c*p.x + s*p.y, -s*p.x + c*p.y);
			}

			float hash(in float2 co) {
				return frac(sin(dot(co.xy ,float2(12.9898,58.233))) * 13758.5453);
			}

			float2 hash2(float2 p) {
				p = float2(dot(p,float2(127.1,311.7)), dot(p,float2(269.5,183.3)));
				return frac(sin(p)*18.5453);
			}

			float psin(float a) {
				return 0.5 + 0.5*sin(a);
			}

			float tanh_approx(float x) {
				float x2 = x*x;
				return clamp(x*(27.0 + x2)/(27.0+9.0*x2), -1.0, 1.0);
			}

			float onoise(float2 x) {
				x *= 0.5;
				float a = sin(x.x);
				float b = sin(x.y);
				float c = lerp(a, b, psin(TAU*tanh_approx(a*b+a+b)));
				
				return c;
			}

			float vnoise(float2 x) {
				float2 i = floor(x);
				float2 w = frac(x);
					
				#if 1
				// quintic interpolation
				float2 u = w*w*w*(w*(w*6.0-15.0)+10.0);
				#else
				// cubic interpolation
				float2 u = w*w*(3.0-2.0*w);
				#endif

				float a = hash(i+float2(0.0,0.0));
				float b = hash(i+float2(1.0,0.0));
				float c = hash(i+float2(0.0,1.0));
				float d = hash(i+float2(1.0,1.0));
					
				float k0 =   a;
				float k1 =   b - a;
				float k2 =   c - a;
				float k3 =   d - c + a - b;

				float aa = lerp(a, b, u.x);
				float bb = lerp(c, d, u.x);
				float cc = lerp(aa, bb, u.y);
				
				return k0 + k1*u.x + k2*u.y + k3*u.x*u.y;
			}

			float fbm(float2 p, int iter) {
				float2 op = p;
				const float aa = 0.45;
				const float pp = 2.03;
				const float2 oo = -float2(1.23, 1.5);
				const float rr = 1.2;
				
				float h = 0.0;
				float d = 0.0;
				float a = 1.0;
				
				for (int i = 0; i < iter; ++i) {
					h += a*onoise(p);
					d += (a);
					a *= aa;
					p += oo;
					p *= pp;
					rot(p, rr);
				}
				
				return lerp((h/d), -0.5*(h/d), pow(vnoise(0.9*op), 0.25));
			}

			float dot2( float2 v ) { return dot(v,v); }
			
			float get_texture_sdf(PdxTextureSampler2D Texture, float2 uv) {
				float sdf = PdxTex2D(Texture, uv).r;
				if ( uv.x < 0. || uv.x > 1. || uv.y < 0. || uv.y > 1. ) {
					return 0.;
				}
				else {
					return sdf;
				}
			}

			float df(float2 uv) {
				float2 texSize = SpriteSize.xy;
				
				float2 sdf1_offset = SpriteBorder[1].xy;
				float2 sdf2_offset = SpriteBorder[2].xy;
				
				float sdf1_scale = SpriteTranslateRotateUVAndAlpha[1].z;
				float sdf2_scale = SpriteTranslateRotateUVAndAlpha[2].z;
				
				//float2 sdf_uv = ( uv + float2(.5,.5) ) * 0.5;
				//sdf_uv.y = 1. - sdf_uv.y;
				float2 sdf1_uv = ( uv - sdf1_offset ) * texSize / SDF_SIZE * sdf1_scale;
				float2 sdf2_uv = ( uv - sdf2_offset ) * texSize / SDF_SIZE * sdf2_scale;
				float sdf1 = get_texture_sdf(ModifyTexture0, sdf1_uv);
				float sdf2 = get_texture_sdf(ModifyTexture1, sdf2_uv);

				float sdflerp = cos(GuiTime * 0.2) * .5 + .5;
				float lerped_sdf = lerp(sdf1, sdf2, sdflerp);
				//float lerped_sdf = lerp(sdf1, sdf2, 0.);

				return 0.5 - lerped_sdf;
			}

			float warp(float2 p, float df) {
				
				float2 off = (1.75 + 0.5*cos(GuiTime*TAU/60.0))*float2(-5, 5);

				float2 op = p + lerp(float2(0.0,0.0), off, 0.5 + 0.5*tanh(df));
				//float2 op = p + 0.5 + 0.5*tanh(df);
				
				float2 v = float2(fbm(op, 5), fbm(p+0.7*float2(1.0, 1.0), 5));
				
				rot(v, 1.0+GuiTime*0.1);
				
				float2 vv = float2(fbm(op + 3.7*v, 7), fbm(op + -2.7*v.yx+0.7*float2(1.0, 1.0), 7));

				rot(vv, -1.0+GuiTime*0.21315);
					
				return fbm(op + 1.4*vv, 3);
			}

			float height(float2 p, float2 global_uv) {
				float sdf = df(global_uv);
				
				float a = 0.005*GuiTime;
				p += 5.0*float2(cos(a), sin(a));
				p *= 2.0;
				p += 13.0;
				float h = warp(p,sdf);
				float rs = 3.0;
				
				float height = 0.35*tanh_approx(rs*h)/rs;
				
				if (sdf <= 0.0) {
					return -height;
				}
				else {
					return height;
				}
			}

			float3 normal(float2 p, float2 global_uv) {
				// As suggested by IQ, thanks!
				float2 eps = -float2(2.0/SpriteSize.y, 0.0);
				
				float3 n;
				
				n.x = height(p + eps.xy, global_uv) - height(p - eps.xy, global_uv);
				n.y = 2.0*eps.x;
				n.z = height(p + eps.yx, global_uv) - height(p - eps.yx, global_uv);
				
				//return normalize(n);
				
				float sdf = -df(global_uv);
				
				float3 bordernormal = normalize( cross( n, float3(-1.0,0.0,-1.0) ) );
				float3 innernormal = normalize( float3(-n.x,n.y,-n.z) );
				
				float mixValueBorder = smoothstep( 0.0, 0.5, sdf );
				mixValueBorder = clamp(mixValueBorder, 0.0, 1.0);
				
				float mixValueInner = smoothstep( 0.0, 0.5, sdf );
				
				float3 border = normalize( lerp( n, bordernormal, mixValueBorder ) );
				float3 inner  = normalize( lerp( n, innernormal, mixValueInner ) );
				
				return border;
			}

			float3 postProcess(float3 col, float2 q)  {
				col=pow(clamp(col,0.0,1.0),float3(0.75,0.75,0.75)); 
				col=col*0.6+0.4*col*col*(3.0-2.0*col);  // contrast
				float sat = dot(col, float3(0.33,0.33,0.33));
				col=lerp(col, float3(sat,sat,sat), -0.4);  // satuation
				col*=0.5+0.5*pow(19.0*q.x*q.y*(1.0-q.x)*(1.0-q.y),0.7);  // vigneting
				return col;
			}

			PDX_MAIN
			{
				float2 q = Input.UV0;
				q.y = 1.0 - q.y;
				float2 p = -1. + 2. * q;
				p.x*=SpriteSize.x/SpriteSize.y;
				
				float mouse_x = SpriteBorder[3].x*2. - 1.;
				float mouse_y = 1. - SpriteBorder[3].y*2.;
				
				//float3 lp1 = float3(0.9, -0.5, 0.8);
				////float3 lp1 = float3(0.75, -0.5, 0.35);
				float3 lp1 = float3(mouse_x, -0.5, mouse_y);
				
				float3 lp2 = float3(-mouse_x, -1.5, -mouse_y);
				////float3 lp2 = float3(-0.9, -1.5, 0.9);
				//float3 lp2 = float3(-0.9, -2.0, -1.3);

				float h = height(p,Input.UV0);
				float3 pp = float3(p.x, h, p.y);
				float ll1 = length(lp1.xz - pp.xz);
				float3 ld1 = normalize(lp1 - pp);
				float3 ld2 = normalize(lp2 - pp);
				
				float3 n = normal(p,Input.UV0);
				float diff1 = max(dot(ld1, n), 0.0);
				float diff2 = max(dot(ld2, n), 0.0);
				
				float3 baseCol = float3(1.0, 0.8, 0.6);
				//float3 lightCol = baseCol.zyx;
				float3 lightCol = float3(1.8, 0.0, 0.4);
				//float3 baseCol = float3(0.6, 0.02, 0.1);
				//float3 lightCol = float3(0.2, 1.3, 2.0);

				float oh = height(p + ll1*0.05*normalize(ld1.xz),Input.UV0);
				const float level0 = 0.0;
				const float level1 = 0.125;
				// VERY VERY fake shadows + hilight
				float3 scol = baseCol*(smoothstep(level0, level1, h) - smoothstep(level0, level1, oh));

				float3 col = float3(0.0,0.0,0.0);
				col += baseCol*pow(diff1, 6.0);
				//col += baseCol*pow(diff1, 3.0);
				col += 0.1*baseCol*pow(diff1, 1.5);
				col += 0.15*lightCol*pow(diff2, 8.0);
				col += 0.015*lightCol*pow(diff2, 2.0);
				col += scol*0.5;

				col = postProcess(col, q);
				
				float alpha = SampleImageSprite(Texture,Input.UV0).a;
				return float4(col, alpha);
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

Effect PODSDFLoadingScreen
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODSDF_LOADINGSCREEN"
}
Effect PODSDFLoadingScreenDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODSDF_LOADINGSCREEN"
	
	Defines = { "DISABLED" }
}

Effect PODSDFLoadingScreen2
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODSDF_LOADINGSCREEN2"
}
Effect PODSDFLoadingScreen2Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODSDF_LOADINGSCREEN2"
	
	Defines = { "DISABLED" }
}