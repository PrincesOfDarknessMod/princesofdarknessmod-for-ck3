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

		static const float4 GH_MARKER_TOP_LEFT_POSTPROCESS = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_STATUE      = float4(0.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_LEFT_ANIM        = float4(0.0f, 0.0f, 1.0f, 0.0f);
		
		static const float4 GH_MARKER_TOP_RIGHT_POSTPROCESS_SMOKE = float4(1.0f, 0.0f, 0.0f, 0.0f);

		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_R              = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_G              = float4(0.0f, 1.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_DIFFUSE_B              = float4(0.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_SSS         = float4(1.0f, 0.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_SPECULARITY = float4(0.0f, 1.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_METALNESS   = float4(1.0f, 1.0f, 1.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_PROPERTIES_ROUGHNESS   = float4(1.0f, 1.0f, 0.0f, 0.0f);
		
		static const float4 GH_MARKER_TOP_RIGHT_ANIM_CONCENTRIC_METAL = float4(1.0f, 0.0f, 0.0f, 0.0f);
		static const float4 GH_MARKER_TOP_RIGHT_ANIM_VERTICAL_SHINIES = float4(0.0f, 1.0f, 0.0f, 0.0f);
		
		static const float POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN = -1.02f;
		static const float POD_PORTRAIT_POSTPROCESS_CHANNEL_MAX = -0.02f;

		// ENUM: postprocessing effects for portraits
		static const uint POD_PORTRAIT_POSTPROCESS_NONE  = 1;
		static const uint POD_PORTRAIT_POSTPROCESS_SMOKE = 2;
		// END ENUM

		// ENUM: animated shaders for portraits
		static const uint POD_PORTRAIT_ANIM_NONE             = 1;
		static const uint POD_PORTRAIT_ANIM_CONCENTRIC_METAL = 2;
		static const uint POD_PORTRAIT_ANIM_VERTICAL_SHINIES = 3;
		// END ENUM

		//
		// Types
		//

		struct GH_SMarkerTexels
		{
			float4 TopLeftTexel;
			float4 TopRightTexel;
		};

		struct GH_SPortraitEffect
		{
			uint  Postprocess;
			uint  AnimType;
			float AnimValue;
			float DiffuseR;
			float DiffuseG;
			float DiffuseB;
			float PropertiesSSS;
			float PropertiesSpecularity;
			float PropertiesMetalness;
			float PropertiesRoughness;
		};

		GH_SPortraitEffect GH_GetDefaultPortraitEffect()
		{
			GH_SPortraitEffect Effect;

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

			return Effect;
		}
	]]
}