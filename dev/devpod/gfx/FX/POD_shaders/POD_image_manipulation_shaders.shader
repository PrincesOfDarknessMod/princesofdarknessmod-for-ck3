# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
	"cw/pdxgui_sprite_textures.fxh"
	"cw/utility.fxh"
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
	
	MainCode PS_EventBackground
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/3dBSW3
			// TODO: move to shared shader file?
			float2x2 rot(float a){
				return float2x2(
					cos(a), -sin(a),
					sin(a), cos(a)
				);
			}

			// float rand(float2 uv){
			// 	return frac(sin(dot(float2(12.9898,78.233), uv)) * 43758.5453123);
			// }
			
			// hash without sine, by dave hoskins https://www.shadertoy.com/view/4djSRW
			// because the trig-based hash functions cause issues on vulkan
			float rand(float2 p) {
				float3 p3 = frac(float3(p.xyx) * .1031);
				p3 += dot(p3, p3.yzx + 33.33);
				return frac((p3.x + p3.y) * p3.z);
			}

			float valueNoise(float2 uv){
				float2 i = frac(uv);
				float2 f = floor(uv);
				float a = rand(f);
				float b = rand(f + float2(1.0, 0.0));
				float c = rand(f + float2(0.0, 1.0));
				float d = rand(f + float2(1.0, 1.0));    
				return lerp(lerp(a, b, i.x), lerp(c, d, i.x), i.y);
			}

			float fbm(float2 uv) {
				float v = 0.0;
				float freq = 9.5;
				float amp = .75;
				float z = (20. * sin(GuiTime * .2)) + 30.;
			
				for (int i = 0; i < 10; ++i) {
					v += valueNoise(uv + (z * uv * .05) + (GuiTime * .1)) * amp;
					uv *= 3.25;        
					amp *= .5;
				}
				
				return v;    
			}

			float4 malkavFBM(float2 uv, float2 TextureSize)
			{
				uv.y = 1.0 - uv.y;
				uv -= .5;

				float2 oldUV = uv;
				uv.x *= TextureSize.x / TextureSize.y;

				uv = mul(uv, rot(GuiTime * .02));
				float2x2 angle = rot(fbm(uv));

				float4 fragColor = float4(float3(
									fbm(mul(float2(4, -1), angle) + uv),
									fbm(mul(float2(5, -2), angle) + uv),
									fbm(mul(float2(6, -3), angle) + uv)), 1.);
				
				// original, more subtle colors:
				//float4 fragColor = float4(float3(
				//					fbm(mul(float2(5.456, -2.8112), angle) + uv),
				//					fbm(mul(float2(5.476, -2.8122), angle) + uv),
				//					fbm(mul(float2(5.486, -2.8132), angle) + uv)
				//				) - (smoothstep(.1, 1., length(oldUV))), 1.);
				return fragColor;
			}

			PDX_MAIN
			{
				float4 OutColor = SampleImageSprite( Texture, Input.UV0 );
				//OutColor *= Input.Color;
				
				float MalkavStrength = SpriteTranslateRotateUVAndAlpha[2].w;
				
				if (MalkavStrength > 0.) {
					float2 TextureSize;
					PdxTex2DSize(Texture, TextureSize);

					float3 BlendedColor = Overlay(OutColor.rgb, malkavFBM(Input.UV0, TextureSize).rgb);

					OutColor.rgb = lerp(OutColor.rgb, BlendedColor, MalkavStrength);
				}

				return OutColor;
			}
		]]
	}

	MainCode PS_PODIMG_GREYSCALE_BLEND
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			PDX_MAIN {
				float4 color = SampleImageSprite(Texture,Input.UV0);
				color *= Input.Color;
				
				float3 bnw_color = DisableColor( color.rgb );
				float bnw_factor = SpriteTranslateRotateUVAndAlpha[1].w;
				
				float3 outcolor = lerp(color.rgb, bnw_color.rgb, bnw_factor);
				
				return float4(outcolor, color.a);
			}
		]]
	}

	MainCode PS_PODIMG_VALUE_TO_ALPHA
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			#define DEFAULT_BLENDFACTOR 0.65
			
			PDX_MAIN {
				float4 color = SampleImageSprite(Texture,Input.UV0);
				color *= Input.Color;
				float3 blendcolor = SpriteModifyTexturesColors[1].rgb;
				#ifdef CUSTOM_BLENDFACTOR
					float blendfactor = SpriteModifyTexturesColors[1].a;
				#else
					float blendfactor = DEFAULT_BLENDFACTOR;
				#endif
				
				float3 color_hsv = RGBtoHSV(color.rgb);
				
				float4 outcolor = float4(blendcolor, color.a*color_hsv.b);
				outcolor.rgb = lerp(color.rgb, blendcolor.rgb, blendfactor);
				
				#ifdef DISABLED
					outcolor.rgb = DisableColor( outcolor.rgb );
				#endif
				
				return outcolor;
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

Effect EventBackground
{
	VertexShader = "VS_Default"
	PixelShader = "PS_EventBackground"
}
Effect EventBackgroundDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_EventBackground"
	
	Defines = { "DISABLED" }
}

Effect PODGreyscaleBlend
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_GREYSCALE_BLEND"
}
Effect PODGreyscaleBlendDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_GREYSCALE_BLEND"
	
	Defines = { "DISABLED" }
}

Effect PODValueToAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_VALUE_TO_ALPHA"
}
Effect PODValueToAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_VALUE_TO_ALPHA"
	
	Defines = { "DISABLED" }
}

Effect PODValueToAlphaCustomBlendfactor
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_VALUE_TO_ALPHA"
	
	Defines = { "CUSTOM_BLENDFACTOR" }
}
Effect PODValueToAlphaCustomBlendfactorDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODIMG_VALUE_TO_ALPHA"
	
	Defines = { "CUSTOM_BLENDFACTOR" "DISABLED" }
}