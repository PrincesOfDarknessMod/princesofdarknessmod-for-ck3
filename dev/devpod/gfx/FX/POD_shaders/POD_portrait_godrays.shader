##
## based on jomini/gfx/FX/jomini/gui_portrait.shader
## also see diffs with game/gfx/FX/gui_painterly_portrait.shader
##

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

			// adapted from https://www.shadertoy.com/view/ls2Xzd
			// Algorithm found in https://medium.com/community-play-3d/god-rays-whats-that-5a67f26aeac2
			// TODO: put in shared shader file
			float4 crepuscular_rays(PdxTextureSampler2D tex, float2 uv, float lod, float2 center) {
				float decay = 0.92;
				float density = 1.0;
				float weight = 0.58767;
				/// NUM_SAMPLES will describe the rays quality, you can play with
				const int nsamples = 50;

				float2 tc = uv.xy;
				float2 deltaTexCoord = tc - center.xy;
				deltaTexCoord *= (1.0 / float(nsamples) * density);
				float illuminationDecay = 1.0;

				float4 color = PdxTex2DLod( tex, tc.xy, lod ) * float4(0.4,0.4,0.4,0.4);
				
				tc += deltaTexCoord * frac( sin(dot(uv.xy+frac(GuiTime), float2(12.9898, 78.233))) * 43758.5453 );
				for (int i = 0; i < nsamples; i++)
				{
					tc -= deltaTexCoord;
					float4 sampl = PdxTex2DLod( tex, tc.xy, lod ) * float4(0.4,0.4,0.4,0.4);

					sampl *= illuminationDecay * weight;
					color += sampl;
					illuminationDecay *= decay;
				}
				
				return color;
			}

			PDX_MAIN
			{
				float2 PortraitUV = Input.UV1;
				PortraitUV /= PortraitUVScale;
				PortraitUV -= PortraitUVOffset / PortraitUVScale;

				//float4 vPortrait   = PdxTex2DLod( Portrait, PortraitUV, Input.Lod );
				float4 vPortrait   = crepuscular_rays( Portrait, PortraitUV, Input.Lod, float2(0.5,0.5) );
				float4 vBackground = PdxTex2DLod0( Background, Input.UV1 );
				float  vMask       = PdxTex2DLod0( Mask, Input.UV1 ).a;

				// fade at the top so the rays don't get cut off abruptly
				vPortrait.a *= smoothstep(0.05, 0.13, PortraitUV.y);
				// fade at the bottom
				//vPortrait.a *= 1.0 - Input.UV1.y;

				float4 vFrame = SampleImageSprite( Frame, Input.UV0 );

				float4 vColor;
				vColor.rgb = vBackground.rgb * vMask;
				vColor.a = vBackground.a * vMask;

								
				if( Input.UV1.y < PopOutThreshold )
 				{
 					vColor = BlendColorPreMultiplied( vColor, vFrame );
 					vColor = BlendColorPreMultiplied( vColor, vPortrait );
 				}
 				else
				{
					vPortrait *= vMask;
					vColor = BlendColorPreMultiplied( vColor, vPortrait );
					vColor = BlendColorPreMultiplied( vColor, vFrame );
				}
				#ifdef DISABLED
					vColor.a *= 0.35;
					vColor.rgb = lerp( vColor.rgb, DisableColor( vColor.rgb ), 0.2 );
				#else
					if ( IsGrayscale > 0.5f )
					{
						vColor.rgb = lerp( vColor.rgb, DisableColor( vColor.rgb ), 0.8 );
						vColor.rgb *= 0.8;
					}
				#endif

				vColor *= Input.Color;
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
