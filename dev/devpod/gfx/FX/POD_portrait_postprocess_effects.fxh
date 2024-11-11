Includes = {
	"GH_portrait_constants.fxh"
	"cw/pdxgui.fxh"
}

PixelShader =
{
	Code [[
		// adapted from https://www.shadertoy.com/view/7tsfWS
		
		// TODO: put hash/noise/FBM/domainwarp functions in shared shader file
		
		float POD_SmokeRand(float2 n) {
			return frac(cos(dot(n, float2(12.9898, 4.1414))) * 43758.5453);
		}

		float POD_SmokeNoise(float2 n) {
			const float2 d = float2(0.0, 1.0);
			float2 b = floor(n), f = smoothstep(float2(0.0,0.0), float2(1.0,1.0), frac(n));
			return lerp(lerp(POD_SmokeRand(b), POD_SmokeRand(b + d.yx), f.x), lerp(POD_SmokeRand(b + d.xy), POD_SmokeRand(b + d.yy), f.x), f.y);
		}

		float POD_SmokeFBM(float2 n) {
			float total = 0.0, amplitude = 1.0;
			for (int i = 0; i < 4; i++) {
				total += POD_SmokeNoise(n) * amplitude;
				n += n;
				amplitude *= 0.5;
			}
			return total;
		}

		float POD_GetSmokeAlpha(in float2 uv)
		{
			uv.y = 1.0 - uv.y;

			float2 TextureSize;
			PdxTex2DSize(MainScene, TextureSize);

			float2 coord = float2(uv.x * TextureSize.x, uv.y * TextureSize.y);
			coord *= float2(1.2, 0.8); // squish for portraits
			float time = GuiTime;

			float2 speed = float2(-0.3, 0.7);
			float2 p = coord.xy * 8.0 / TextureSize.xx;
			float q = POD_SmokeFBM(p - time * 0.1);
			float2 r = float2(POD_SmokeFBM(p + q + time * speed.x - p.x - p.y), POD_SmokeFBM(p + q - time * speed.y));
			//float c = lerp(0.0, 1.0, POD_SmokeFBM(p + r)) + lerp(0.0, 0.5, r.x) - lerp(0.0, 1.0, r.y);
			float c = lerp(0.2, 1.0, POD_SmokeFBM(p + r)) + lerp(0.0, 0.5, r.x) - lerp(0.0, 1.2, r.y);

			c = clamp(c, 0.0, 1.0);
			//float alpha = 1.0 - (c * 0.8);
			float alpha = 1.0 - c;
			return alpha;
		}

		void POD_TryApplyPostEffect(inout float4 Color, in float2 uv)
		{
			// Smoke
			if ( Color.r >= POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN && Color.r <= POD_PORTRAIT_POSTPROCESS_CHANNEL_MAX )
			{
				// hacky solution to prevent ugly aliased outline
				// (check ssao.shader or ssao_apply.shader for a more permanent solution)
				if (Color.a > 0.996) {
					Color.r -= POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN;
				}
				Color.a *= POD_GetSmokeAlpha(uv);
			}
			//Color = crepuscular_rays(uv, float2(0.5,0.5));
		}
	]]
}