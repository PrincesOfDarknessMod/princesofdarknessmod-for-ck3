Includes = {
	"jomini/portrait_decals.fxh"
	"cw/camera.fxh"
	"cw/pdxgui.fxh"
	"cw/utility.fxh"
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

		void GH_TryApplyStatueEffect(in GH_SPortraitEffect PortraitEffect, inout float4 Diffuse, inout float4 Properties, inout float3 Normal, in VS_OUTPUT_PDXMESHPORTRAIT Input)
		{
			if (PortraitEffect.isEnabled)
			{
				if ( PortraitEffect.DiffuseR != -1.0f ) {
					Diffuse.r = lerp(Diffuse.r, PortraitEffect.DiffuseR, PortraitEffect.ColorLerp );
				}
				if ( PortraitEffect.DiffuseG != -1.0f ) {
					Diffuse.g = lerp(Diffuse.g, PortraitEffect.DiffuseG, PortraitEffect.ColorLerp );
				}
				if ( PortraitEffect.DiffuseB != -1.0f ) {
					Diffuse.b = lerp(Diffuse.b, PortraitEffect.DiffuseB, PortraitEffect.ColorLerp );
				}
				if ( PortraitEffect.PropertiesSSS != -1.0f ) {
					Properties.r = lerp(Properties.r, PortraitEffect.PropertiesSSS, PortraitEffect.PropertiesLerp );
				}
				if ( PortraitEffect.PropertiesSpecularity != -1.0f ) {
					Properties.g = lerp(Properties.g, PortraitEffect.PropertiesSpecularity, PortraitEffect.PropertiesLerp );
				}
				if ( PortraitEffect.PropertiesMetalness != -1.0f ) {
					Properties.b = lerp(Properties.b, PortraitEffect.PropertiesMetalness, PortraitEffect.PropertiesLerp );
				}
				if ( PortraitEffect.PropertiesRoughness != -1.0f ) {
					Properties.a = lerp(Properties.a, PortraitEffect.PropertiesRoughness, PortraitEffect.PropertiesLerp );
				}

				if ( PortraitEffect.AnimType == POD_PORTRAIT_ANIM_CONCENTRIC_METAL ) {
					// the value of the gene controls animation speed
					float metalSpeed   = GuiTime * 2.0 / PortraitEffect.AnimValue;
					float normalsSpeed = GuiTime * 1.2 / PortraitEffect.AnimValue;

					float adjustedDepth = length(CameraPosition.xz - Input.WorldSpacePos.xz) * 0.5;
					float pulseDepthForMetal   = (sin( adjustedDepth - metalSpeed   ) + 1.0) / 2.0;
					float pulseDepthForNormals = (sin( adjustedDepth - normalsSpeed ) - 1.0);
					pulseDepthForNormals -= 0.1 - (pulseDepthForNormals * 0.1);

					Properties.b *= pulseDepthForMetal; // metalness

					float adjustedHeight = (CameraPosition.y - Input.WorldSpacePos.y) * 0.3;
					float pulseHeight = (sin( adjustedHeight + normalsSpeed ) + 3.0) / 4.0; // value between 0.5 and 1.0

					float3 Normal2 = normalize( float3(Normal.x, Normal.y, pulseDepthForNormals) );
					Normal = normalize(lerp(Normal,Normal2,pulseHeight));
				}
				else if ( PortraitEffect.AnimType == POD_PORTRAIT_ANIM_VERTICAL_SHINIES ) {
					// the value of the gene controls animation speed
					float speed = GuiTime * 2.0 / PortraitEffect.AnimValue;

					float adjustedHeight = (CameraPosition.y - Input.WorldSpacePos.y) * 0.3;
					float pulseHeight = (sin( adjustedHeight - speed ) + 1.0) / 2.0;

					Properties.g *= pulseHeight * 2.0; // specularity
				}

				if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_FIRE ) {
					float speed = GuiTime * 0.6;

					float c = cos(speed);
					float s = sin(speed);
					// rotation along Z-axis
					Normal = normalize( mul( Normal, float3x3(
						float3(c, -s, 0),
						float3(s, c, 0),
						float3(0, 0, 1)
					) ) );
				}
			}
		}

		void POD_TryApplyStatueLighting(in GH_SPortraitEffect PortraitEffect, in float3 Normal, inout float3 Color)
		{
			if (PortraitEffect.isEnabled)
			{
				if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_FIRE ) {
					float edgeGlow = 1.0 - abs( dot( normalize(CameraLookAtDir), Normal ) );
					Color = ColorDodge(Color, edgeGlow);
				}
			}
		}

		void POD_RemapColorsForPostEffect(inout PS_COLOR_SSAO Out, in GH_SPortraitEffect PortraitEffect)
		{
			if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_SMOKE ) {
				Out.Color.r += POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN;
				Out.SSAOColor = float4(0.0f, 0.0f, 0.0f, 0.0f);
			}
			else if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_FIRE && PortraitEffect.isEnabled ) {
				Out.Color.b += POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN;
				Out.SSAOColor = float4(0.0f, 0.0f, 0.0f, 0.0f);
			}
			else if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_FOGOFWAR ) {
				Out.Color = float4(0.0f, 0.0f, 0.0f, Out.Color.a / 2.0f);
				Out.SSAOColor = float4(0.0f, 0.0f, 0.0f, 0.0f);
			}
			else if ( PortraitEffect.Postprocess == POD_PORTRAIT_POSTPROCESS_INVISIBLE ) {
				Out.Color.a = 0.0f;
				Out.SSAOColor = float4(0.0f, 0.0f, 0.0f, 0.0f);
			}
		}

		void POD_SetScriptedClothingColors(inout float3 Sample, in int index, in GH_SPortraitEffect PortraitEffect)
		{
			if (index < POD_CLOTHING_CHANNELS) {
				if ( PortraitEffect.ClothingColors[index].r != -1.0f ) {
					Sample.r = PortraitEffect.ClothingColors[index].r;
				}
				if ( PortraitEffect.ClothingColors[index].g != -1.0f ) {
					Sample.g = PortraitEffect.ClothingColors[index].g;
				}
				if ( PortraitEffect.ClothingColors[index].b != -1.0f ) {
					Sample.b = PortraitEffect.ClothingColors[index].b;
				}
			}
		}
		
		//
		// Macros
		//

		#ifndef PDX_OPENGL
			#define GH_PdxTex2DArrayLoad(samp,uvi,lod) (samp)._Texture.Load( int4((uvi), (lod)) )
		#else
			#define GH_PdxTex2DArrayLoad texelFetch
		#endif
		
		//
		// Service
		//

		bool POD_GeneWeightEquals(float GeneToCheck, float TargetWeight)
		{
			return abs(GeneToCheck - TargetWeight) <= POD_PORTRAIT_GENE_CHECK_TOLERANCE;
		}

		bool GH_MarkerTexelEquals(float4 MarkerTexel0, float4 MarkerTexel1)
		{
			return distance(MarkerTexel0, MarkerTexel1) < GH_MARKER_CHECK_TOLERANCE;
		}

		float GH_MipLevelToLod(float MipLevel)
		{
			// This function (originally GetMIP6Level()) was graciously provided by Buck (EK2).

			#ifndef PDX_OPENGL
				// If running on DX, use the below to get decal texture size.
				float3 TextureSize;
				DecalDiffuseArray._Texture.GetDimensions( TextureSize.x , TextureSize.y , TextureSize.z );
			#else
				// If running on OpenGL, use the below to get decal texture size.
				ivec3 TextureSize = textureSize(DecalDiffuseArray, 0);
			#endif

			// Get log base 2 for current texture size (1024px - 10, 512px - 9, etc.)
			// Take that away from 10 to find the current MIP level.
			// Take that away from MipLevel to find which MIP We need to sample in the texture buffer to retrieve the "absolute" MIP6 containing our encoded pixels

			return MipLevel - (10.0f - log2(TextureSize.x));
		}

		GH_SMarkerTexels GH_ExtractMarkerTexels(uint DiffuseIndex)
		{
			// Max pixel coordinate for the GH_MARKER_MIP_LEVEL-th mip-map.
			// TODO: Actually use a formula based on GH_MARKER_MIP_LEVEL here, instead of a literal?
			static const int MAX_MARKER_PIXEL_COORD = 15; // 6th mip-map is 16x16 for decals

			static int MarkerLod = int(GH_MipLevelToLod(GH_MARKER_MIP_LEVEL));

			static const int2 TOP_LEFT_UV     = int2(0, 0);
			static const int2 TOP_RIGHT_UV    = int2(MAX_MARKER_PIXEL_COORD, 0);
			// static const int2 BOTTOM_RIGHT_UV = int2(MAX_MARKER_PIXEL_COORD, MAX_MARKER_PIXEL_COORD);
			// static const int2 BOTTOM_LEFT_UV  = int2(0, MAX_MARKER_PIXEL_COORD);

			GH_SMarkerTexels MarkerTexels;
			MarkerTexels.TopLeftTexel     = GH_PdxTex2DArrayLoad(DecalDiffuseArray, int3(TOP_LEFT_UV, DiffuseIndex), MarkerLod);
			MarkerTexels.TopRightTexel    = GH_PdxTex2DArrayLoad(DecalDiffuseArray, int3(TOP_RIGHT_UV, DiffuseIndex), MarkerLod);

			// #ifndef PIXEL_SHADER
			// 	MarkerTexels.BottomRightTexel = GH_PdxTex2DArrayLoad(DecalDiffuseArray, int3(BOTTOM_RIGHT_UV, DiffuseIndex), MarkerLod);
			// 	MarkerTexels.BottomLeftTexel  = GH_PdxTex2DArrayLoad(DecalDiffuseArray, int3(BOTTOM_LEFT_UV, DiffuseIndex), MarkerLod);
			// #else
			// 	// The other two corners are not currently used by pixel shaders, so no use sampling them from there.
			// 	MarkerTexels.BottomRightTexel = float4(0.0f, 0.0f, 0.0f, 0.0f);
			// 	MarkerTexels.BottomLeftTexel  = float4(0.0f, 0.0f, 0.0f, 0.0f);
			// #endif // !PIXEL_SHADER

			return MarkerTexels;
		}

		//
		// Interface
		//

		GH_SPortraitEffect GH_ScanMarkerDecals(int DecalsCount, bool isAttachment, bool isSkin)
		{
			int From = 0;
			int To   = DecalsCount;

			// NOTE: The following is based on AddDecals() and needs
			//       to be kept in sync with it on vanilla updates.
			const int TEXEL_COUNT_PER_DECAL = 15;
			int FromDataTexel = From * TEXEL_COUNT_PER_DECAL;
			int ToDataTexel   = To * TEXEL_COUNT_PER_DECAL;

			static const uint MAX_VALUE = 65535;
			// END NOTE

			GH_SPortraitEffect Effect = GH_GetDefaultPortraitEffect();

			for (int i = FromDataTexel; i <= ToDataTexel; i += TEXEL_COUNT_PER_DECAL)
			{
				DecalData Data = GetDecalData(i);

				// TODO: Filter by bodypart index for an early continue?

				if (Data._DiffuseIndex >= MAX_VALUE || Data._Weight <= 0.001f)
					continue;

				GH_SMarkerTexels MarkerTexels = GH_ExtractMarkerTexels(Data._DiffuseIndex);

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
					float PostprocessGeneWeight = Data._Weight;
					if (POD_GeneWeightEquals(PostprocessGeneWeight, POD_GENE_WEIGHT_POSTPROCESS_FOGOFWAR)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_FOGOFWAR;
					}
					else if (POD_GeneWeightEquals(PostprocessGeneWeight, POD_GENE_WEIGHT_POSTPROCESS_INVISIBLE)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_INVISIBLE;
					}
					else if (POD_GeneWeightEquals(PostprocessGeneWeight, POD_GENE_WEIGHT_POSTPROCESS_SMOKE)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_SMOKE;
					}
					else if (POD_GeneWeightEquals(PostprocessGeneWeight, POD_GENE_WEIGHT_POSTPROCESS_FIRE)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_FIRE;
					}
					/*if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_POSTPROCESS_SMOKE)) {
						Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_SMOKE;
					}*/
				}
				else if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_CLOTHING)) {
					if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_1_R)) {
						Effect.ClothingColors[0].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_1_G)) {
						Effect.ClothingColors[0].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_1_B)) {
						Effect.ClothingColors[0].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_2_R)) {
						Effect.ClothingColors[1].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_2_G)) {
						Effect.ClothingColors[1].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_2_B)) {
						Effect.ClothingColors[1].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_3_R)) {
						Effect.ClothingColors[2].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_3_G)) {
						Effect.ClothingColors[2].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_3_B)) {
						Effect.ClothingColors[2].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_4_R)) {
						Effect.ClothingColors[3].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_4_G)) {
						Effect.ClothingColors[3].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_4_B)) {
						Effect.ClothingColors[3].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_5_R)) {
						Effect.ClothingColors[4].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_5_G)) {
						Effect.ClothingColors[4].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_5_B)) {
						Effect.ClothingColors[4].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_6_R)) {
						Effect.ClothingColors[5].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_6_G)) {
						Effect.ClothingColors[5].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_6_B)) {
						Effect.ClothingColors[5].b = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_7_R)) {
						Effect.ClothingColors[6].r = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_7_G)) {
						Effect.ClothingColors[6].g = Data._Weight;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CLOTHING_7_B)) {
						Effect.ClothingColors[6].b = Data._Weight;
					}
				}
				else if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_CONDITIONAL))
				{
					float ConditionalGeneWeight = Data._Weight;
					if (POD_GeneWeightEquals(ConditionalGeneWeight, POD_GENE_WEIGHT_CONDITIONAL_IGNORECLOTHING)) {
						Effect.isEnabled = !isAttachment;
					}
					else if (POD_GeneWeightEquals(ConditionalGeneWeight, POD_GENE_WEIGHT_CONDITIONAL_CLOTHINGONLY)) {
						Effect.isEnabled = isAttachment;
					}
					else if (POD_GeneWeightEquals(ConditionalGeneWeight, POD_GENE_WEIGHT_CONDITIONAL_JURATA)) {
						Effect.isEnabled = isSkin;
						Effect.ColorLerp = 0.4f;
					}
					/*if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CONDITIONAL_IGNORECLOTHING)) {
						Effect.isEnabled = !isAttachment;
					}
					else if (GH_MarkerTexelEquals(MarkerTexels.TopRightTexel, GH_MARKER_TOP_RIGHT_CONDITIONAL_SKINONLY)) {
						Effect.isEnabled = isSkin;
					}*/
				}
			}

			return Effect;
		}
	]]
}