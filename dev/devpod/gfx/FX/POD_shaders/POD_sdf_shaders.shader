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
				
				//float2 sdf_uv = ( p + float2(.5,.5) ) * 1.25;
				float2 sdf_uv = ( uv - float2(.5,.15) ) * texSize / SDF_SIZE * 0.9;
				float podsdf  = get_texture_sdf(ModifyTexture0, sdf_uv);
				float ankhsdf = get_texture_sdf(ModifyTexture1, sdf_uv);

				float sdflerp = cos(GuiTime * 0.2) * .5 + .5;
				float lerped_sdf = lerp(podsdf, ankhsdf, sdflerp);

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
				col=lerp(col, float3(saturator,saturator,saturator), -0.4);  // satuation
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

				col = float3(col.r, 0.0, col.r*col.r*col.r*col.r*col.r*0.25);

				float alpha = 1.0 - ( (1.0 - col.r) * (1.0 - SampleImageSprite(Texture,Input.UV0).a) );

				//float alpha = 1.0;

				// if (uv.y >= 0.91 || uv.y <= 0.09) {
				// 	alpha = 0.0;
				// }

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