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
			#define BLENDFACTOR 0.65
			
			PDX_MAIN {
				float4 color = SampleImageSprite(Texture,Input.UV0);
				color *= Input.Color;
				float3 blendcolor = SpriteModifyTexturesColors[1].rgb;
				
				float3 color_hsv = RGBtoHSV(color.rgb);
				
				float4 outcolor = float4(blendcolor, color.a*color_hsv.b);
				outcolor.rgb = lerp(color.rgb, blendcolor.rgb, BLENDFACTOR);
				
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