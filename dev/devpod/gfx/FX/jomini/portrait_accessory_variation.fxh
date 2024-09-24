Includes = {
	"jomini/texture_decals_base.fxh"
	"jomini/portrait_user_data.fxh"

	# CfV (POD)
	"GH_portrait_effects.fxh"
	# CfV end
}

PixelShader =
{
	TextureSampler PatternMask
	{
		Ref = PdxMeshCustomTexture0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}

	TextureSampler PatternColorPalette
	{
		Ref = PdxMeshCustomTexture1
		MagFilter = "Point"
		MinFilter = "Point"
		MipFilter = "Point"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}

	TextureSampler PatternColorMasks
	{
		Ref = PdxMeshCustomTexture2
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
		type = "2darray"
	}

	TextureSampler PatternNormalMaps
	{
		Ref = PdxMeshCustomTexture3
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
		type = "2darray"
	}

	TextureSampler PatternPropertyMaps
	{
		Ref = PdxMeshCustomTexture4
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
		type = "2darray"
	}

	Code
	[[
		#ifdef VARIATIONS_ENABLED
			struct SPatternOutput
			{
				float4	_Diffuse;
				float4	_Properties;
				float3	_Normal;
			};

			// CfV (POD)
			SPatternOutput ApplyPattern( float2 UV, SPatternDesc Desc, float RandomNumber, int MaskIndex, inout float OpacityMask, GH_SPortraitEffect PortraitEffect )
			// CfV end
			{
				// Rotate and scale around (0.5,0.5)
				float2 Rotate = float2( cos( Desc._Rotation ), sin( Desc._Rotation ) );
				UV -= vec2( 0.5f);
				UV = float2( UV.x * Rotate.x - UV.y * Rotate.y, UV.x * Rotate.y + UV.y * Rotate.x );
				UV /= Desc._Scale;
				UV += vec2( 0.5f );
				UV += Desc._Offset;

				float4 ColorMask = PdxTex2D( PatternColorMasks, float3( UV, Desc._ColorMaskIndex ) );

				float4 PatternColor = float4( 1.0f, 1.0f, 1.0f, 0 );
				float4 PatternProperties = PdxTex2D( PatternPropertyMaps, float3( UV, Desc._PropertyMapIndex ) );
				float4 PatternNormalSample = PdxTex2D( PatternNormalMaps, float3( UV, Desc._NormalMapIndex ) );

				//Sample the color palette once for each channel in the mask
				for ( int i = 0; i < 4; ++i )
				{
					if ( ColorMask[i] > 0.0f )
					{
						// Select from 16-width color palette
						float3 Sample;
						if ( PatternColorOverrides[MaskIndex + i].a > 0.0f )
						{
							Sample = PatternColorOverrides[MaskIndex + i].rgb;
						}
						else
						{
							float HorizontalSample = ( MaskIndex * 4.0f ) + i;
							HorizontalSample = ( HorizontalSample + 0.5f ) / 16.0f;
							Sample = PdxTex2D( PatternColorPalette, float2( HorizontalSample, RandomNumber ) ).rgb;
							// CfV (POD)
							POD_SetScriptedClothingColors(Sample, MaskIndex + i, PortraitEffect);
							// CfV end
						}
						PatternColor.rgb = lerp( PatternColor.rgb, Sample, ColorMask[i] );
						PatternColor.a = max( PatternColor.a, ColorMask[i] );
					}
				}

				SPatternOutput PatternOutput;
				PatternOutput._Diffuse = PatternColor;
				PatternOutput._Diffuse.a = Desc._UseOpacity ? PatternNormalSample.b : 1.0f; // Set alpha (normalmap blue channel)
				PatternOutput._Normal = UnpackDecalNormal( PatternNormalSample, PatternColor.a );
				PatternOutput._Properties = PatternProperties;

				OpacityMask = min( ( ColorMask[0] + ColorMask[1] + ColorMask[2] + ColorMask[3] ), 1 );
				return PatternOutput;
			}

			// CfV (POD)
			void ApplyVariationPatterns( in VS_OUTPUT_PDXMESHPORTRAIT Input, inout float4 Diffuse, inout float4 Properties, inout float3 NormalSample, GH_SPortraitEffect PortraitEffect )
			// CfV end
			{
				float4 Mask = PdxTex2D( PatternMask, Input.UV0 );
				float4 PatternDiffuse = float4( 1.0f, 1.0f, 1.0f, 1.0f );
				float3 PatternNormal = float3( 0.0f, 0.0f, 1.0f );
				float4 PatternProperties = Properties;

				float RandomNumber = GetRandomNumber( Input.InstanceIndex );
				for( int i = 0; i < 4; ++i )
				{
					if( Mask[i] > 0.0f )
					{
						float OpacityMask = 0;
						// CfV (POD)
						SPatternOutput PatternOutput = ApplyPattern( Input.UV1, GetPatternDesc( Input.InstanceIndex, i ), RandomNumber, i, OpacityMask, PortraitEffect );
						// CfV end

						PatternDiffuse = lerp( PatternDiffuse, PatternOutput._Diffuse, Mask[i] * OpacityMask);
						PatternNormal = lerp( PatternNormal, PatternOutput._Normal.rgb, Mask[i] * OpacityMask);
						PatternProperties = lerp( PatternProperties, PatternOutput._Properties, Mask[i] * OpacityMask);
					}
				}

				Diffuse *= PatternDiffuse;
				Diffuse.rgb *= PatternProperties.rrr; // pattern AO

				NormalSample = normalize( OverlayNormal( NormalSample, PatternNormal ) );
				Properties = PatternProperties;
			}
			void ApplyClothFresnel( in VS_OUTPUT_PDXMESHPORTRAIT Input,in float3  CameraPosition, in float3  Normal, inout float3 Color )
			{
				float4 Mask = PdxTex2D( PatternMask, Input.UV0 );
				for( int i = 0; i < 4; ++i )
				{
					if( Mask[i] > 0.0f )
					{
						SPatternDesc Desc = GetPatternDesc( Input.InstanceIndex, i );
						float3 ViewVector = normalize( CameraPosition - Input.WorldSpacePos );
						float VdotN = saturate( dot( Normal, ViewVector ) ) + 1e-5;
						float CottonLike = pow( 1 - VdotN, Desc._InnerExp ) * Desc._InnerScale;
						float SilkLike = pow( VdotN, Desc._RimExp ) * Desc._RimScale;
						float ClothFresnel = CottonLike + SilkLike;
						Color = Color * max( 0, ClothFresnel );
					}
				}
			}
		#endif
	]]
}
