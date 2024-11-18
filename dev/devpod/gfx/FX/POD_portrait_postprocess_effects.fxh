Includes = {
	"GH_portrait_constants.fxh"
	"cw/pdxgui.fxh"
	"cw/utility.fxh"
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
		
		
		#define FIRESPEED float2(0.0,-0.1)
		
		float POD_FireHash(in float2 co) {
			return frac(sin(dot(co.xy ,float2(12.9898,58.233))) * 13758.5453);
		}
		
		float POD_FireNoise(float2 p){
			float2 ip = floor(p);
			float2 u = frac(p);
			u = u*u*(3.0-2.0*u);
			float res = lerp(
				lerp(POD_FireHash(ip),POD_FireHash(ip+float2(1.0,0.0)),u.x),
				lerp(POD_FireHash(ip+float2(0.0,1.0)),POD_FireHash(ip+float2(1.0,1.0)),u.x),u.y);
			return res*res;
		}
		
		float POD_FireFBM( in float2 x )
		{   
			const float H = 0.8;
			float G = exp2(-H);
			float f = 1.0;
			float a = 1.0;
			float t = 0.0;
			for( int i=0; i<12; i++ )
			{
				t += a*POD_FireNoise(f * x - GuiTime * FIRESPEED);
				f *= 2.0;
				a *= G;
			}
			//return t;
			return smoothstep(0.,1.8,t);
		}
		
		float POD_FireDomainwarp( in float2 p )
		{
			float2 q = float2( POD_FireFBM( p + float2(0.0,0.0) ),
						POD_FireFBM( p + float2(5.2,1.3) ) );
			float2 r = float2( POD_FireFBM( p + 4.0*q + float2(1.7,9.2) ),
						POD_FireFBM( p + 4.0*q + float2(8.3,2.8) ) );
			return POD_FireFBM( p + 4.0*r );
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
			// Fire
			else if ( Color.b >= POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN && Color.b <= POD_PORTRAIT_POSTPROCESS_CHANNEL_MAX )
			{
				if (Color.a > 0.996) {
					Color.b -= POD_PORTRAIT_POSTPROCESS_CHANNEL_MIN;
				}
				float fire = 1.0 - POD_FireDomainwarp(uv);
				Color.g *= fire;
				//Color.g = lerp(Color.g * fire * fire, Color.g, Color.r);
				Color.b *= fire*fire*fire*fire*fire;
				//Color.a *= fire;
				Color.a = lerp(Color.a * fire, Color.a, Color.r); // more transparency in shadowy areas
			}
		}
	]]
}