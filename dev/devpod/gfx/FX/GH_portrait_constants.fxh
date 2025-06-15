PixelShader =
{
	Code [[
		// The general approach of encoding technical information via marker pixels in a decal mip-map
		// is adapted from a much more sophisticated implementation made by shader wizard Buck for EK2.

		//
		// Constants
		//

		// Marker enabling various effects is encoded via reserved RGBA values for top-left
		// and top-right pixels at this mip level of relevant decals' diffuse textures.
		static const int GH_MARKER_MIP_LEVEL = 6;

		static const float GH_MARKER_CHECK_TOLERANCE = 0.01f;

		static const float POD_PORTRAIT_GENE_CHECK_TOLERANCE = 0.01f;


		static const float4 GH_MARKER_TOP_LEFT_POSTPROCESS = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_STATUE      = float4(0.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_ANIM        = float4(0.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_CLOTHING    = float4(1.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_CONDITIONAL = float4(0.0f, 1.0f, 1.0f, 0.0f);
		

		//static const float4 GH_MARKER_TOP_RIGHT_POSTPROCESS_SMOKE = float4(1.0f, 0.0f, 0.0f, 0.0f);


		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_R              = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_G              = float4(0.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_B              = float4(0.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_SSS         = float4(1.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_SPECULARITY = float4(0.0f, 1.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_METALNESS   = float4(1.0f, 1.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_ROUGHNESS   = float4(1.0f, 1.0f, 0.0f, 0.0f);
		

		static const float4 GH_MARKER_TOP_RIGHT_ANIM_CONCENTRIC_METAL = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_ANIM_VERTICAL_SHINIES = float4(0.0f, 1.0f, 0.0f, 0.0f);
		

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_1_R = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_1_G = float4(0.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_1_B = float4(0.0f, 0.0f, 1.0f, 0.0f);

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_2_R = float4(50.0f, 0.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_2_G = float4(0.0f, 50.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_2_B = float4(0.0f, 0.0f, 50.0f, 0.0f)/255.0f;

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_3_R = float4(100.0f, 0.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_3_G = float4(0.0f, 100.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_3_B = float4(0.0f, 0.0f, 100.0f, 0.0f)/255.0f;

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_4_R = float4(150.0f, 0.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_4_G = float4(0.0f, 150.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_4_B = float4(0.0f, 0.0f, 150.0f, 0.0f)/255.0f;

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_5_R = float4(200.0f, 0.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_5_G = float4(0.0f, 200.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_5_B = float4(0.0f, 0.0f, 200.0f, 0.0f)/255.0f;

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_6_R = float4(1.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_6_G = float4(0.0f, 1.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_6_B = float4(1.0f, 0.0f, 1.0f, 0.0f);

		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_7_R = float4(50.0f, 50.0f, 0.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_7_G = float4(0.0f, 50.0f, 50.0f, 0.0f)/255.0f;
		static const float4 GH_MARKER_TOP_RIGHT_CLOTHING_7_B = float4(50.0f, 0.0f, 50.0f, 0.0f)/255.0f;
		

		//static const float4 GH_MARKER_TOP_RIGHT_CONDITIONAL_IGNORECLOTHING = float4(1.0f, 0.0f, 0.0f, 0.0f);
		//static const float4 GH_MARKER_TOP_RIGHT_CONDITIONAL_SKINONLY       = float4(0.0f, 1.0f, 0.0f, 0.0f);
		

		static const float POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN = -1.02f;
		static const float POD_PORTRAIT_POSTPROCESS_CHANNEL_MAX = -0.02f;

		// ENUM: postprocessing effects for portraits (2d)
		static const uint POD_PORTRAIT_POSTPROCESS_NONE      = 1;
		static const uint POD_PORTRAIT_POSTPROCESS_FOGOFWAR  = 2;
		static const uint POD_PORTRAIT_POSTPROCESS_INVISIBLE = 3;
		static const uint POD_PORTRAIT_POSTPROCESS_SMOKE     = 4;
		static const uint POD_PORTRAIT_POSTPROCESS_FIRE      = 5;
		// END ENUM

		// ENUM: animated shaders for portraits (3d)
		static const uint POD_PORTRAIT_ANIM_NONE             = 1;
		static const uint POD_PORTRAIT_ANIM_CONCENTRIC_METAL = 2;
		static const uint POD_PORTRAIT_ANIM_VERTICAL_SHINIES = 3;
		// END ENUM

		static const float POD_GENE_WEIGHT_POSTPROCESS_FOGOFWAR  = 0.1f;
		static const float POD_GENE_WEIGHT_POSTPROCESS_INVISIBLE = 0.2f;
		static const float POD_GENE_WEIGHT_POSTPROCESS_SMOKE     = 0.3f;
		static const float POD_GENE_WEIGHT_POSTPROCESS_FIRE      = 0.4f;

		static const float POD_GENE_WEIGHT_CONDITIONAL_IGNORECLOTHING = 0.1f;
		static const float POD_GENE_WEIGHT_CONDITIONAL_CLOTHINGONLY   = 0.2f;
		static const float POD_GENE_WEIGHT_CONDITIONAL_JURATA         = 0.3f;
		static const float POD_GENE_WEIGHT_CONDITIONAL_IGNOREEYES     = 0.4f;
		static const float POD_GENE_WEIGHT_CONDITIONAL_DOLL           = 0.5f;

		//
		// Types
		//

		struct GH_SMarkerTexels
		{
			float4 TopLeftTexel;
			float4 TopRightTexel;
		};

		static const int POD_CLOTHING_CHANNELS = 7;

		struct GH_SPortraitEffect
		{
			bool   isEnabled;
			float  ColorLerp;
			float  PropertiesLerp;
			uint   Postprocess;
			uint   AnimType;
			float  AnimValue;
			float  DiffuseR;
			float  DiffuseG;
			float  DiffuseB;
			float  PropertiesSSS;
			float  PropertiesSpecularity;
			float  PropertiesMetalness;
			float  PropertiesRoughness;
			// only the first 7 channels are used by the game
			float3 ClothingColors[7];
		};

		GH_SPortraitEffect GH_GetDefaultPortraitEffect()
		{
			GH_SPortraitEffect Effect;

			Effect.isEnabled = true;

			Effect.ColorLerp      = 1.0f;
			Effect.PropertiesLerp = 1.0f;

			Effect.Postprocess = POD_PORTRAIT_POSTPROCESS_NONE;

			Effect.AnimType  = POD_PORTRAIT_ANIM_NONE;
			Effect.AnimValue = 1.0f;

			// using negative values tells the shader to skip these
			Effect.DiffuseR              = -1.0f;
			Effect.DiffuseG              = -1.0f;
			Effect.DiffuseB              = -1.0f;
			Effect.PropertiesSSS         = -1.0f;
			Effect.PropertiesSpecularity = -1.0f;
			Effect.PropertiesMetalness   = -1.0f;
			Effect.PropertiesRoughness   = -1.0f;

			Effect.ClothingColors[0] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[1] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[2] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[3] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[4] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[5] = float3(-1.0f, -1.0f, -1.0f);
			Effect.ClothingColors[6] = float3(-1.0f, -1.0f, -1.0f);

			return Effect;
		}
	]]
}