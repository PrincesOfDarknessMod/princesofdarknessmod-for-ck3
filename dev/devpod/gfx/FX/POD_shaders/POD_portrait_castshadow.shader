##
## based on jomini/gfx/FX/jomini/gui_portrait.shader
## also see diffs with game/gfx/FX/gui_painterly_portrait.shader
##

## usage: add this to a portrait_button
## shaderfile = "gfx/FX/POD_shaders/POD_portrait_castshadow.shader"
## the color property sets the color of the cast shadow:
## color = { 0.0 0.3 1.0 1.0 }
## the portrait_offset property sets the distance (in UVs) of the shadow:
## portrait_offset = { -0.01 -0.01 }

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
}

VertexStruct VS_OUTPUT_PORTRAIT
{
	float4 Position		: PDX_POSITION;
	float2 UV0			: TEXCOORD0;
	float2 UV1			: TEXCOORD1;
	float4 Color		: COLOR;
	float  Lod			: TEXCOORD2;
};

ConstantBuffer( 2 )
{
	float2	WidgetPos;
	float2	WidgetSize;
	float3	HighlightColor;
	float	PopOutThreshold;
	float2	PortraitUVOffset;
	float2	PortraitUVScale;
	float2	PortraitTextureSize;
	float	IsGrayscale;
}

VertexShader =
{
	MainCode VertexShader
	{
		Input = "VS_INPUT_PDX_GUI"
		Output = "VS_OUTPUT_PORTRAIT"
		Code
		[[
			PDX_MAIN
			{
				VS_OUTPUT_PORTRAIT Out;
				float2 PixelPos = WidgetLeftTop + Input.LeftTop_WidthHeight.xy + Input.Position * Input.LeftTop_WidthHeight.zw;
				Out.Position = PixelToScreenSpace( PixelPos );
				Out.UV0 = Input.UVLeftTop_WidthHeight.xy + Input.Position * Input.UVLeftTop_WidthHeight.zw;
				Out.UV1 = (PixelPos - WidgetPos) / WidgetSize;
				Out.Color = Input.Color;

				float2 SizeRatio = PortraitTextureSize / WidgetSize;
				Out.Lod = floor( log2( min( SizeRatio.x, SizeRatio.y ) ) );

				return Out;
			}
		]]
	}
}


PixelShader =
{
	TextureSampler Frame
	{
		Index = 0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}

	TextureSampler Mask
	{
		Index = 1
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}

	TextureSampler Portrait
	{
		Index = 2
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}

	TextureSampler Background
	{
		Index = 3
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}

	MainCode PixelShader
	{
		Input = "VS_OUTPUT_PORTRAIT"
		Output = "PDX_COLOR"
		Code
		[[
			// replacements for unused input values
			#define DEFAULT_UV_OFFSET float2(0.,0.)

			//Blends Front on top of Back using Front's alpha channel
			float4 BlendColor( in float4 Back, in float4 Front )
			{
				float4 Color;
				Color.rgb = Front.rgb*Front.a + Back.rgb*Back.a * ( 1.0f - Front.a );
				Color.a = Front.a + Back.a * ( 1.0f - Front.a );
				Color.rgb /= Color.a;
				return Color;
			}
			float4 BlendColorPreMultiplied( in float4 Back, in float4 Front )
			{
				return Front + Back * ( 1.0f - Front.a );
			}
			PDX_MAIN
			{
				float2 PortraitUV = Input.UV1;
				PortraitUV /= PortraitUVScale;
				PortraitUV -= DEFAULT_UV_OFFSET / PortraitUVScale;

				float4 vPortrait   = PdxTex2DLod( Portrait, PortraitUV, Input.Lod );
				float4 vBackground = PdxTex2DLod0( Background, Input.UV1 );
				float  vMask       = PdxTex2DLod0( Mask, Input.UV1 ).a;

				float4 vPortraitShadow = float4( Input.Color.rgb, PdxTex2DLod( Portrait, PortraitUV + PortraitUVOffset, Input.Lod ).a * Input.Color.a );

				float4 vFrame = SampleImageSprite( Frame, Input.UV0 );

				float4 vColor;
				vColor.rgb = vBackground.rgb * vMask;
				vColor.a = vBackground.a * vMask;

				float4 vColorShadow;
				vColorShadow.rgb = vBackground.rgb * vMask;
				vColorShadow.a = vBackground.a * vMask;

				if( Input.UV1.y < PopOutThreshold )
 				{
 					vColor = BlendColorPreMultiplied( vColor, vFrame );
 					vColor = BlendColorPreMultiplied( vColor, vPortrait );
 					vColorShadow = BlendColorPreMultiplied( vColorShadow, vFrame );
 					vColorShadow = BlendColorPreMultiplied( vColorShadow, vPortraitShadow );
 				}
 				else
				{
					vPortrait *= vMask;
					vPortraitShadow *= vMask;
					vColor = BlendColorPreMultiplied( vColor, vPortrait );
					vColor = BlendColorPreMultiplied( vColor, vFrame );
 					vColorShadow = BlendColorPreMultiplied( vColorShadow, vFrame );
 					vColorShadow = BlendColorPreMultiplied( vColorShadow, vPortraitShadow );
				}
				#ifdef DISABLED
					vColor.a *= 0.35;
					vColor.rgb = lerp( vColor.rgb, DisableColor( vColor.rgb ), 0.2 );
				#else
					if ( IsGrayscale > 0.5f )
					{
						// fully desaturate the color instead of just doing 80%
						//vColor.rgb = lerp( vColor.rgb, DisableColor( vColor.rgb ), 0.8 );
						//vColor.rgb *= 0.8;
						vColor.rgb = DisableColor( vColor.rgb );
					}
				#endif
				
				vColor = lerp(vColorShadow, vColor, vColor.a);

				// Color used for shadow instead
				//vColor *= Input.Color;
				#ifndef NO_HIGHLIGHT
					vColor.rgb += HighlightColor * vColor.a;
				#endif
			    return vColor;
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

DepthStencilState DepthStencilState
{
	DepthEnable = no
}

Effect PdxGuiPortrait
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" }
}

Effect Up
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" }
}

Effect Over
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" }
}

Effect Down
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" }
}

Effect Disabled
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "DISABLED" "PDX_GUI_CORNERED_SPRITE_SUPPORT" "NO_HIGHTLIGHT" }
}

Effect NoHighlightUp
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" "NO_HIGHLIGHT" }
}

Effect NoHighlightOver
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" "NO_HIGHLIGHT" }
}

Effect NoHighlightDown
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "PDX_GUI_CORNERED_SPRITE_SUPPORT" "NO_HIGHLIGHT" }
}

Effect NoHighlightDisabled
{
	VertexShader = "VertexShader"
	PixelShader = "PixelShader"

	Defines = { "DISABLED" "PDX_GUI_CORNERED_SPRITE_SUPPORT" "NO_HIGHTLIGHT" "NO_HIGHLIGHT" }
}
