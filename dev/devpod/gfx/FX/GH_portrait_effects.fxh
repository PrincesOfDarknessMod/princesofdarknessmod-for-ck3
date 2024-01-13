Includes = {
	"jomini/portrait_decals.fxh"
	"cw/camera.fxh"
	"cw/pdxgui.fxh"
	"GH_portrait_constants.fxh"
}

PixelShader =
{
	Code [[
		// The general approach of encoding technical information via marker pixels in a decal mip-map
		// is adapted from a much more sophisticated implementation made by shader wizard Buck for EK2.

		//
		// Interface
		//

		void GH_TryApplyStatueEffect(in GH_SPortraitEffect PortraitEffect, inout float4 Diffuse, inout float4 Properties, in VS_OUTPUT_PDXMESHPORTRAIT Input)
		{
			if ( PortraitEffect.DiffuseR              != -1.0f ) { Diffuse.r    = PortraitEffect.DiffuseR;              }
			if ( PortraitEffect.DiffuseG              != -1.0f ) { Diffuse.g    = PortraitEffect.DiffuseG;              }
			if ( PortraitEffect.DiffuseB              != -1.0f ) { Diffuse.b    = PortraitEffect.DiffuseB;              }
			if ( PortraitEffect.PropertiesSSS         != -1.0f ) { Properties.r = PortraitEffect.PropertiesSSS;         }
			if ( PortraitEffect.PropertiesSpecularity != -1.0f ) { Properties.g = PortraitEffect.PropertiesSpecularity; }
			if ( PortraitEffect.PropertiesMetalness   != -1.0f ) { Properties.b = PortraitEffect.PropertiesMetalness;   }
			if ( PortraitEffect.PropertiesRoughness   != -1.0f ) { Properties.a = PortraitEffect.PropertiesRoughness;   }

			if ( PortraitEffect.AnimType == POD_PORTRAIT_ANIM_CONCENTRIC_METAL ) {
				// the value of the gene controls animation speed
				float iTime = GuiTime * 2.0 / PortraitEffect.AnimValue;

				float adjustedDepth = length(CameraPosition.xz - Input.WorldSpacePos.xz) * 0.5;
				float pulseDepth = (sin( adjustedDepth  - iTime ) + 1.0) / 2.0;

				Properties.b *= pulseDepth; // metalness
			}
			else if ( PortraitEffect.AnimType == POD_PORTRAIT_ANIM_VERTICAL_SHINIES ) {
				// the value of the gene controls animation speed
				float iTime = GuiTime * 2.0 / PortraitEffect.AnimValue;

				float adjustedHeight = (CameraPosition.y - Input.WorldSpacePos.y) * 0.3;
				float pulseHeight = (sin( adjustedHeight  - iTime ) + 1.0) / 2.0;

				Properties.g *= pulseHeight * 2.0; // specularity
			}
		}

		void POD_RemapColorsForPostEffect(inout PS_COLOR_SSAO Out, in GH_SPortraitEffect PortraitEffect)
		{
			if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_SMOKE ) {
				Out.Color.r += POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN;
				Out.SSAOColor = float4(0.0f, 0.0f, 0.0f, 0.0f);
			}
		}
		
		//
		// Service
		//

		bool GH_MarkerTexelEquals(float4 MarkerTexel0, float4 MarkerTexel1)
		{
			return distance(MarkerTexel0, MarkerTexel1) < GH_MARKER_CHECK_TOLERANCE;
		}

		float2 GH_ToDecalUV(DecalData Data, float U, float V)
		{
			float AtlasFactor = 1.0f / Data._AtlasSize;

			return ( float2(U, V) - Data._UVOffset ) + ( Data._AtlasPos * AtlasFactor );
		}

		float GH_MipLevelToLod(float MipLevel)
		{
			// This function (originally GetMIP6Level()) was graciously provided by Buck (EK2).

			#ifdef PDX_DIRECTX_11
				// If running on DX, use the below to get decal texture size.
				float3 TextureSize;
				DecalDiffuseArray._Texture.GetDimensions( TextureSize.x , TextureSize.y , TextureSize.z );
			#else
				#ifdef PDX_VULKAN
				// If running on VULKAN, use the below to get decal texture size.
				float3 TextureSize;
				DecalDiffuseArray._Texture.GetDimensions( TextureSize.x , TextureSize.y , TextureSize.z );
				#else
				// If running on OpenGL, use the below to get decal texture size.
				ivec3 TextureSize = textureSize(DecalDiffuseArray, 0);
				#endif
			#endif

			// Get log base 2 for current texture size (1024px - 10, 512px - 9, etc.)
			// Take that away from 10 to find the current MIP level.
			// Take that away from MipLevel to find which MIP We need to sample in the texture buffer to retrieve the "absolute" MIP6 containing our encoded pixels

			return MipLevel - (10.0f - log2(TextureSize.x));
		}

		GH_SMarkerTexels GH_ExtractMarkerTexels(DecalData Data)
		{
			static float MarkerLod = GH_MipLevelToLod(GH_MARKER_MIP_LEVEL);

			float2 TopLeftDecalUV  = GH_ToDecalUV(Data, 0.0f, 0.0f);
			float2 TopRightDecalUV = GH_ToDecalUV(Data, 1.0f, 0.0f);

			GH_SMarkerTexels MarkerTexels;
			MarkerTexels.TopLeftTexel  = PdxTex2DLod(DecalDiffuseArray, float3(TopLeftDecalUV,  Data._DiffuseIndex), MarkerLod);
			MarkerTexels.TopRightTexel = PdxTex2DLod(DecalDiffuseArray, float3(TopRightDecalUV, Data._DiffuseIndex), MarkerLod);

			return MarkerTexels;
		}

		//
		// Interface
		//

		GH_SPortraitEffect GH_ScanMarkerDecals(int DecalsCount)
		{
			int From = 0;
			int To   = DecalsCount;

			// NOTE: The following is based on AddDecals() and needs
			//       to be kept in sync with it on vanilla updates.
			const int TEXEL_COUNT_PER_DECAL = 13;
			int FromDataTexel = From * TEXEL_COUNT_PER_DECAL;
			int ToDataTexel   = To * TEXEL_COUNT_PER_DECAL;

			const uint MAX_VALUE = 65535;
			// END NOTE

			GH_SPortraitEffect Effect = GH_GetDefaultPortraitEffect();

			for (int i = FromDataTexel; i <= ToDataTexel; i += TEXEL_COUNT_PER_DECAL)
			{
				DecalData Data = GetDecalData(i, MAX_VALUE);

				// TODO: Filter by bodypart index for an early continue?

				if (Data._DiffuseIndex >= MAX_VALUE || Data._Weight <= 0.001f)
					continue;

				GH_SMarkerTexels MarkerTexels = GH_ExtractMarkerTexels(Data);

				if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_STATUE))
				{
					if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_DIFFUSE_R)) {
						Effect.DiffuseR = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_DIFFUSE_G)) {
						Effect.DiffuseG = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_DIFFUSE_B)) {
						Effect.DiffuseB = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_PROPERTIES_SSS)) {
						Effect.PropertiesSSS = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_PROPERTIES_SPECULARITY)) {
						Effect.PropertiesSpecularity = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_PROPERTIES_METALNESS)) {
						Effect.PropertiesMetalness = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_PROPERTIES_ROUGHNESS)) {
						Effect.PropertiesRoughness = Data._Weight;
					}
				}
				else if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_ANIM)) {
					Effect.AnimValue = Data._Weight;
					if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_ANIM_CONCENTRIC_METAL)) {
						Effect.AnimType = POD_PORTRAIT_ANIM_CONCENTRIC_METAL;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_ANIM_VERTICAL_SHINIES)) {
						Effect.AnimType = POD_PORTRAIT_ANIM_VERTICAL_SHINIES;
					}
				}
				else if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_POSTPROCESS)) {
					if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_POSTPROCESS_SMOKE)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_SMOKE;
					}
				}
			}

			return Effect;
		}
	]]
}