includes = {
	"jomini/portrait_decal_utils.fxh"
	"jomini/portrait_user_data.fxh"
	# MOD(godherja)
	"GH_portrait_effects.fxh"
	# END MOD
}

PixelShader =
{
	TextureSampler DecalDiffuseArray
	{
		Ref = JominiPortraitDecalDiffuseArray
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
		type = "2darray"
	}

	TextureSampler DecalNormalArray
	{
		Ref = JominiPortraitDecalNormalArray
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
		type = "2darray"
	}

	TextureSampler DecalPropertiesArray
	{
		Ref = JominiPortraitDecalPropertiesArray
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
		type = "2darray"
	}

	BufferTexture DecalDataBuffer
	{
		Ref = JominiPortraitDecalData
		type = uint
	}

	Code
	[[		
		// Should match SPortraitDecalTextureSet::BlendMode
		#define BLEND_MODE_OVERLAY 0
		#define BLEND_MODE_REPLACE 1
		#define BLEND_MODE_HARD_LIGHT 2
		#define BLEND_MODE_MULTIPLY 3
		// Special handling of normal Overlay blend mode (in shader only)
		#define BLEND_MODE_OVERLAY_NORMAL 4

		float OverlayDecal( float Target, float Blend )
		{
			return float( Target > 0.5f ) * ( 1.0f - ( 2.0f * ( 1.0f - Target ) * ( 1.0f - Blend ) ) ) +
				   float( Target <= 0.5f ) * ( 2.0f * Target * Blend );
		}

		float HardLightDecal( float Target, float Blend )
		{
			return float( Blend > 0.5f ) * ( 1.0f - ( 2.0f * ( 1.0f - Target ) * ( 1.0f - Blend ) ) ) +
				   float( Blend <= 0.5f ) * ( 2.0f * Target * Blend );
		}

		float4 BlendDecal( uint BlendMode, float4 Target, float4 Blend, float Weight )
		{
			float4 Result = vec4( 0.0f );

			if ( BlendMode == BLEND_MODE_OVERLAY )
			{
				Result = float4( OverlayDecal( Target.r, Blend.r ), OverlayDecal( Target.g, Blend.g ),
								 OverlayDecal( Target.b, Blend.b ), OverlayDecal( Target.a, Blend.a ) );
			}
			else if ( BlendMode == BLEND_MODE_REPLACE )
			{
				Result = Blend;
			}
			else if ( BlendMode == BLEND_MODE_HARD_LIGHT )
			{
				Result = float4( HardLightDecal( Target.r, Blend.r ), HardLightDecal( Target.g, Blend.g ),
								 HardLightDecal( Target.b, Blend.b ), HardLightDecal( Target.a, Blend.a ) );
			}
			else if ( BlendMode == BLEND_MODE_MULTIPLY )
			{
				Result = Target * Blend;
			}
			else if ( BlendMode == BLEND_MODE_OVERLAY_NORMAL )
			{
				Result = float4( OverlayNormal( Target.xyz, Blend.xyz ), Target.a );
			}

			return lerp( Target, Result, Weight );
		}

		struct DecalData
		{
			uint _DiffuseIndex;
			uint _NormalIndex;
			uint _PropertiesIndex;
			uint _BodyPartIndex;

			uint _DiffuseBlendMode;
			uint _NormalBlendMode;
			uint _PropertiesBlendMode;
			float _Weight;

			uint2 _AtlasPos;
			float2 _UVOffset;

			uint _AtlasSize;
		};

		DecalData GetDecalData( int Index, uint MaxValue )
		{
			// Data for each decal is stored in multiple texels as specified by DecalData

			DecalData Data;

			Data._DiffuseIndex = PdxReadBuffer( DecalDataBuffer, Index );
			Data._NormalIndex = PdxReadBuffer( DecalDataBuffer, Index + 1 );
			Data._PropertiesIndex = PdxReadBuffer( DecalDataBuffer, Index + 2 );
			Data._BodyPartIndex = PdxReadBuffer( DecalDataBuffer, Index + 3 );

			Data._DiffuseBlendMode = PdxReadBuffer( DecalDataBuffer, Index + 4 );
			Data._NormalBlendMode = PdxReadBuffer( DecalDataBuffer, Index + 5 );
			if ( Data._NormalBlendMode == BLEND_MODE_OVERLAY )
			{
				Data._NormalBlendMode = BLEND_MODE_OVERLAY_NORMAL;
			}
			Data._PropertiesBlendMode = PdxReadBuffer( DecalDataBuffer, Index + 6 );
			Data._Weight = float( PdxReadBuffer( DecalDataBuffer, Index + 7 ) ) / MaxValue;

			Data._AtlasPos = uint2( PdxReadBuffer( DecalDataBuffer, Index + 8 ), PdxReadBuffer( DecalDataBuffer, Index + 9 ) );
			Data._UVOffset = float2( PdxReadBuffer( DecalDataBuffer, Index + 10 ), PdxReadBuffer( DecalDataBuffer, Index + 11 ) );
			Data._UVOffset /= MaxValue;

			Data._AtlasSize = PdxReadBuffer( DecalDataBuffer, Index + 12 );

			return Data;
		}

		// MOD(godherja)

		//
		// Service
		//

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
				// If running on OpenGL, use the below to get decal texture size.
				ivec3 TextureSize = textureSize(DecalDiffuseArray, 0);
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
			MarkerTexels.TopLeftTexel  = PdxTex2DLod(DecalDiffuseArray, float3(TopLeftDecalUV, Data._DiffuseIndex), MarkerLod);
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

			GH_SPortraitEffect Effect;
			Effect.Type  = GH_PORTRAIT_EFFECT_TYPE_NONE;
			Effect.Param = float4(0.0f, 0.0f, 0.0f, 0.0f);

			for (int i = FromDataTexel; i <= ToDataTexel; i += TEXEL_COUNT_PER_DECAL)
			{
				DecalData Data = GetDecalData(i, MAX_VALUE);

				// TODO: Filter by bodypart index for an early continue?

				if (Data._DiffuseIndex >= MAX_VALUE || Data._Weight <= 0.001f)
					continue;

				GH_SMarkerTexels MarkerTexels = GH_ExtractMarkerTexels(Data);

				//if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_FLAT))
					//Effect.Type = GH_PORTRAIT_EFFECT_TYPE_FLAT;

				if (GH_MarkerTexelEquals(MarkerTexels.TopLeftTexel, GH_MARKER_TOP_LEFT_STATUE))
					Effect.Type = GH_PORTRAIT_EFFECT_TYPE_STATUE;

				if (Effect.Type != GH_PORTRAIT_EFFECT_TYPE_NONE)
				{
					Effect.Param = MarkerTexels.TopRightTexel;
					break;
				}
			}

			return Effect;
		}
		// END MOD

		void AddDecals( inout float3 Diffuse, inout float3 Normals, inout float4 Properties, float2 UV, uint InstanceIndex, int From, int To )
		{
			// Body part index is scripted on the mesh asset and should match ECharacterPortraitPart
			uint BodyPartIndex = GetBodyPartIndex( InstanceIndex );

			const int TEXEL_COUNT_PER_DECAL = 13;
			int FromDataTexel = From * TEXEL_COUNT_PER_DECAL;
			int ToDataTexel = To * TEXEL_COUNT_PER_DECAL;

			const uint MAX_VALUE = 65535;

			// Sorted after priority
			for ( int i = FromDataTexel; i <= ToDataTexel; i += TEXEL_COUNT_PER_DECAL )
			{
				DecalData Data = GetDecalData( i, MAX_VALUE );

				// Max index => unused
				if ( Data._BodyPartIndex == BodyPartIndex )
				{
					float Weight = Data._Weight;

					// Assumes that the cropped area size corresponds to the atlas factor
					float AtlasFactor = 1.0f / Data._AtlasSize;
					if ( ( ( UV.x >= Data._UVOffset.x ) && ( UV.x < ( Data._UVOffset.x + AtlasFactor ) ) ) &&
						 ( ( UV.y >= Data._UVOffset.y ) && ( UV.y < ( Data._UVOffset.y + AtlasFactor ) ) ) )
					{
						float2 DecalUV = ( UV - Data._UVOffset ) + ( Data._AtlasPos * AtlasFactor );

						if ( Data._DiffuseIndex < MAX_VALUE )
						{
							float4 DiffuseSample = PdxTex2D( DecalDiffuseArray, float3( DecalUV, Data._DiffuseIndex ) );
							Weight = DiffuseSample.a * Weight;
							Diffuse = BlendDecal( Data._DiffuseBlendMode, float4( Diffuse, 0.0f ), DiffuseSample, Weight ).rgb;
						}

						if ( Data._NormalIndex < MAX_VALUE )
						{
							float3 NormalSample = UnpackDecalNormal( PdxTex2D( DecalNormalArray, float3( DecalUV, Data._NormalIndex ) ), Weight );
							Normals = BlendDecal( Data._NormalBlendMode, float4( Normals, 0.0f ), float4( NormalSample, 0.0f ), Weight ).xyz;
						}

						if ( Data._PropertiesIndex < MAX_VALUE )
						{
							float4 PropertiesSample = PdxTex2D( DecalPropertiesArray, float3( DecalUV, Data._PropertiesIndex ) );
							Properties = BlendDecal( Data._PropertiesBlendMode, Properties, PropertiesSample, Weight );
						}
					}
				}
			}

			Normals = normalize( Normals );
		}
	]]
}
