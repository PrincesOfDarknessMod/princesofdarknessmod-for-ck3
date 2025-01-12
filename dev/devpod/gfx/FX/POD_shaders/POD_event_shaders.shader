# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
	"cw/utility.fxh"
	"standardfuncsgfx.fxh"
}

VertexShader =
{
	MainCode VS_Default
	{
		Input = "VS_INPUT_PDX_GUI"
		Output = "VS_OUTPUT_PDX_GUI"
		Code
		[[
			PDX_MAIN
			{
				return PdxGuiDefaultVertexShader( Input );
			}
		]]
	}
}

PixelShader =
{
	TextureSampler Texture
	{
		Ref = PdxTexture0
		MagFilter = "Point"
		MinFilter = "Point"
		MipFilter = "Point"
		SampleModeU = "Clamp"
		SampleModeV = "Clamp"
	}
	MainCode PS_Default
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			PDX_MAIN
			{
				float4 OutColor = SampleImageSprite( Texture, Input.UV0 );
				OutColor *= Input.Color;
				
				#ifdef DISABLED
					OutColor.rgb = DisableColor( OutColor.rgb );
				#endif
				
			    return OutColor;
			}
		]]
	}
	MainCode PS_EventBackground
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/3dBSW3
			// TODO: move to shared shader file?
			float2x2 rot(float a){
				return float2x2(
					cos(a), -sin(a),
					sin(a), cos(a)
				);
			}

			float rand(float2 uv){
				return frac(sin(dot(float2(12.9898,78.233), uv)) * 43758.5453123);
			}

			float valueNoise(float2 uv){
				float2 i = frac(uv);
				float2 f = floor(uv);
				float a = rand(f);
				float b = rand(f + float2(1.0, 0.0));
				float c = rand(f + float2(0.0, 1.0));
				float d = rand(f + float2(1.0, 1.0));    
				return lerp(lerp(a, b, i.x), lerp(c, d, i.x), i.y);
			}

			float fbm(float2 uv) {
				float v = 0.0;
				float freq = 9.5;
				float amp = .75;
				float z = (20. * sin(GuiTime * .2)) + 30.;
			
				for (int i = 0; i < 10; ++i) {
					v += valueNoise(uv + (z * uv * .05) + (GuiTime * .1)) * amp;
					uv *= 3.25;        
					amp *= .5;
				}
				
				return v;    
			}

			float4 malkavFBM(float2 uv, float2 TextureSize)
			{
				uv.y = 1.0 - uv.y;
				uv -= .5;

				float2 oldUV = uv;
				uv.x *= TextureSize.x / TextureSize.y;

				uv = mul(uv, rot(GuiTime * .02));
				float2x2 angle = rot(fbm(uv));

				float4 fragColor = float4(float3(
									fbm(mul(float2(4, -1), angle) + uv),
									fbm(mul(float2(5, -2), angle) + uv),
									fbm(mul(float2(6, -3), angle) + uv)), 1.);
				
				// original, more subtle colors:
				//float4 fragColor = float4(float3(
				//					fbm(mul(float2(5.456, -2.8112), angle) + uv),
				//					fbm(mul(float2(5.476, -2.8122), angle) + uv),
				//					fbm(mul(float2(5.486, -2.8132), angle) + uv)
				//				) - (smoothstep(.1, 1., length(oldUV))), 1.);
				return fragColor;
			}

			PDX_MAIN
			{
				float4 OutColor = SampleImageSprite( Texture, Input.UV0 );
				//OutColor *= Input.Color;
				
				float MalkavStrength = SpriteTranslateRotateUVAndAlpha[2].w;
				
				if (MalkavStrength > 0.) {
					float2 TextureSize;
					PdxTex2DSize(Texture, TextureSize);

					float3 BlendedColor = Overlay(OutColor.rgb, malkavFBM(Input.UV0, TextureSize).rgb);

					OutColor.rgb = lerp(OutColor.rgb, BlendedColor, MalkavStrength);
				}

				return OutColor;
			}
		]]
	}
	MainCode PS_ColorDisplay
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			PDX_MAIN
			{
				float a = SampleImageSprite( Texture, Input.UV0 ).a;

				float input_r = SpriteTranslateRotateUVAndAlpha[1].w;
				float input_g = SpriteTranslateRotateUVAndAlpha[2].w;
				float input_b = SpriteTranslateRotateUVAndAlpha[3].w;

				float3 input_rgb = float3(input_r,input_g,input_b);
				float3 output_rgb;
				
				#if defined(HUE_GRADIENT)
					float3 input_hsv = RGBtoHSV(input_rgb);
					input_hsv.r = Input.UV0.x;
					output_rgb = HSVtoRGB(input_hsv);
				#elif defined(SATURATION_GRADIENT)
					float3 input_hsv = RGBtoHSV(input_rgb);
					input_hsv.g = Input.UV0.x;
					output_rgb = HSVtoRGB(input_hsv);
				#elif defined(VALUE_GRADIENT)
					float3 input_hsv = RGBtoHSV(input_rgb);
					input_hsv.b = Input.UV0.x;
					output_rgb = HSVtoRGB(input_hsv);
				#else
					#ifdef RED_GRADIENT
						output_rgb.r = Input.UV0.x;
					#else
						output_rgb.r = input_r;
					#endif
					
					#ifdef GREEN_GRADIENT
						output_rgb.g = Input.UV0.x;
					#else
						output_rgb.g = input_g;
					#endif
					
					#ifdef BLUE_GRADIENT
						output_rgb.b = Input.UV0.x;
					#else
						output_rgb.b = input_b;
					#endif
				#endif
				
				return float4(output_rgb,a);
			}
		]]
	}
	MainCode PS_Unmoored
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/ldBSRd

			float2 random2(float2 c) { float j = 4906.0*sin(dot(c,float2(169.7, 5.8))); float2 r; r.x = frac(512.0*j); j *= .125; r.y = frac(512.0*j);return r-0.5;}

			static const float F2 =  0.3660254;
			static const float G2 = -0.2113249;

			float simplex2d(float2 p){float2 s = floor(p + (p.x+p.y)*F2),x = p - s - (s.x+s.y)*G2; float e = step(0.0, x.x-x.y); float2 i1 = float2(e, 1.0-e),  x1 = x - i1 - G2, x2 = x - 1.0 - 2.0*G2; float3 w, d; w.x = dot(x, x); w.y = dot(x1, x1); w.z = dot(x2, x2); w = max(0.5 - w, 0.0); d.x = dot(random2(s + 0.0), x); d.y = dot(random2(s +  i1), x1); d.z = dot(random2(s + 1.0), x2); w *= w; w *= w; d *= w; return dot(d, float3(70.0,70.0,70.0));}

			float3 rgb2yiq(float3 color){return mul( color, float3x3(0.299,0.587,0.114,0.596,-0.274,-0.321,0.211,-0.523,0.311) );}
			float3 yiq2rgb(float3 color){return mul( color, float3x3(1.,0.956,0.621,1,-0.272,-0.647,1.,-1.107,1.705) );}

			float3 convertRGB443quant(float3 color){ float3 out0 = mod(color,1./16.); out0.b = mod(color.b, 1./8.); return out0;}
			float3 convertRGB443(float3 color){return color-convertRGB443quant(color);}

			float2 sincos( float x ){return float2(sin(x), cos(x));}
			float2 rotate2d(float2 uv, float phi){float2 t = sincos(phi); return float2(uv.x*t.y-uv.y*t.x, uv.x*t.x+uv.y*t.y);}
			float3 rotate3d(float3 p, float3 v, float phi){ v = normalize(v); float2 t = sincos(-phi); float s = t.x, c = t.y, x =-v.x, y =-v.y, z =-v.z; float4x4 M = float4x4(x*x*(1.-c)+c,x*y*(1.-c)-z*s,x*z*(1.-c)+y*s,0.,y*x*(1.-c)+z*s,y*y*(1.-c)+c,y*z*(1.-c)-x*s,0.,z*x*(1.-c)-y*s,z*y*(1.-c)+x*s,z*z*(1.-c)+c,0.,0.,0.,0.,1.);return (mul(float4(p,1.),M)).xyz;}

			float varazslat(float2 position, float time){
				float color = 0.0;
				float t = 2.*time;
				color += sin(position.x*cos(t/10.0)*20.0 )+cos(position.x*cos(t/15.)*10.0 );
				color += sin(position.y*sin(t/ 5.0)*15.0 )+cos(position.x*sin(t/25.)*20.0 );
				color += sin(position.x*sin(t/10.0)*  .2 )+sin(position.y*sin(t/35.)*10.);
				color *= sin(t/10.)*.5;
				
				return color;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				float time = GuiTime * 1.1;
				uv = (uv-.5)*3.;
				
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv.x *= TextureSize.x / TextureSize.y;
			
				float3 vlsd = float3(0,1,0);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				vlsd = rotate3d(vlsd, float3(1.,1.,0.), time);
				
				float2 
					v0 = .75 * sincos(.3457 * time + .3423) - simplex2d(uv * .917),
					v1 = .75 * sincos(.7435 * time + .4565) - simplex2d(uv * .521), 
					v2 = .75 * sincos(.5345 * time + .3434) - simplex2d(uv * .759);
				
				float3 color = float3(dot(uv-v0, vlsd.xy),dot(uv-v1, vlsd.yz),dot(uv-v2, vlsd.zx));
				
				color *= .2 + 2.5*float3(
					(16.*simplex2d(uv+v0) + 8.*simplex2d((uv+v0)*2.) + 4.*simplex2d((uv+v0)*4.) + 2.*simplex2d((uv+v0)*8.) + simplex2d((v0+uv)*16.))/32.,
					(16.*simplex2d(uv+v1) + 8.*simplex2d((uv+v1)*2.) + 4.*simplex2d((uv+v1)*4.) + 2.*simplex2d((uv+v1)*8.) + simplex2d((v1+uv)*16.))/32.,
					(16.*simplex2d(uv+v2) + 8.*simplex2d((uv+v2)*2.) + 4.*simplex2d((uv+v2)*4.) + 2.*simplex2d((uv+v2)*8.) + simplex2d((v2+uv)*16.))/32.
				);
				
				color = yiq2rgb(color);
				
				color *= 1.- .25* float3(
					varazslat(uv *.25, time + .5),
					varazslat(uv * .7, time + .2),
					varazslat(uv * .4, time + .7)
				);
				
				color = float3(0.1 + (color.r * 0.9), 0.15, color.b);
				
				// background blend
				//float background = 1. * smoothstep(1.0,0.,length(uv));
				//background = 1. - background;
				//color.b = lerp(color.b, background, 0.2);

				color = float3(pow(color.r, 0.4), color.g, pow(color.b, 0.4));

				return float4(color, SampleImageSprite(Texture,Input.UV0).a);
			}
		]]
	}
	MainCode PS_Kaleidoscope
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/WsSGWG

			float2x2 rot(float x)
			{
				return float2x2(cos(x), sin(x), -sin(x), cos(x));
			}

			float2 foldRotate(in float2 p, in float s) {
				//float a = PI / s - atan(p.x, p.y);
				float a = PI / s - atan2(p.y, p.x);
				float n = PI * 2. / s;
				a = floor(a / n) * n;
				p = mul(p, rot(a));
				return p;
			}

			float sdRect( float2 p, float2 b )
			{
				float2 d = abs(p) - b;
				return min(max(d.x, d.y),0.0) + length(max(d,0.0));
			}

			// TheGrid by dila
			// https://www.shadertoy.com/view/llcXWr
			float tex(float2 p, float z)
			{
				p = foldRotate(p, 8.0);
				float2 q = (frac(p / 10.0) - 0.5) * 10.0;
				for (int i = 0; i < 3; ++i) {
					for(int j = 0; j < 2; j++) {
						q = abs(q) - .25;
						q = mul(q, rot(PI * .25));
					}
					q = abs(q) - float2(1.0, 1.5);
					q = mul(q, rot(PI * .25 * z));
					q = foldRotate(q, 3.0);  
				}
				float d = sdRect(q, float2(1., 1.));
				float f = 1.0 / (1.0 + abs(d));
				return smoothstep(.9, 1., f);
			}

			// The Drive Home by BigWings
			// https://www.shadertoy.com/view/MdfBRX
			float Bokeh(float2 p, float2 sp, float size, float mi, float blur)
			{
				float d = length(p - sp);
				float c = smoothstep(size, size*(1.-blur), d);
				c *= lerp(mi, 1., smoothstep(size*.8, size, d));
				return c;
			}

			float2 hash( float2 p ){
				p = float2( dot(p,float2(127.1,311.7)),dot(p,float2(269.5,183.3)));
				return frac(sin(p)*43758.5453) * 2.0 - 1.0;
			}

			float dirt(float2 uv, float n)
			{
				float2 p = frac(uv * n);
				float2 st = (floor(uv * n) + 0.5) / n;
				float2 rnd = hash(st);
				return Bokeh(p, float2(0.5, 0.5) + float2(0.2,0.2) * rnd, 0.05, abs(rnd.y * 0.4) + 0.3, 0.25 + rnd.x * rnd.y * 0.2);
			}

			float sm(float start, float end, float t, float smo)
			{
				return smoothstep(start, start + smo, t) - smoothstep(end - smo, end, t);
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				uv = uv * 2.0 - 1.0;
				
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv.x *= TextureSize.x / TextureSize.y * 1.4;
				uv.x -= 0.8;
				uv *= 2.0;
				
				float3 col = float3(0.0, 0.0, 0.0);
				#define N 3
				#define NN float(N)
				#define INTERVAL 6.0
				#define INTENSITY1 (NN * INTERVAL - t) / (NN * INTERVAL)
				#define INTENSITY float3(INTENSITY1, INTENSITY1, INTENSITY1)
				
				float time = GuiTime * 0.4;

				for(int i = 0; i < N; i++) {
					float t;
					float ii = float(N - i);
					t = ii * INTERVAL - mod(time - INTERVAL * 0.75, INTERVAL);
					col = lerp(col, INTENSITY, dirt(mod(uv * max(0.0, t) * 0.1 + float2(.2, -.2) * time, 1.2), 3.5));
					
					t = ii * INTERVAL - mod(time + INTERVAL * 0.5, INTERVAL);
					col = lerp(col, INTENSITY * float3(0.7, 0.8, 1.0) * 1.3,tex(uv * max(0.0, t), 4.45));
					
					t = ii * INTERVAL - mod(time - INTERVAL * 0.25, INTERVAL);
					col = lerp(col, INTENSITY * float3(1.,1.,1.), dirt(mod(uv * max(0.0, t) * 0.1 + float2(-.2, -.2) *  time, 1.2), 3.5));
					
					t = ii * INTERVAL - mod(time, INTERVAL);
					float r = length(uv * 2.0 * max(0.0, t));
					float rr = sm(-24.0, -0.0, (r - mod(time * 30.0, 90.0)), 10.0);
					col = lerp(col, lerp(INTENSITY * float3(1.,1.,1.), INTENSITY * float3(0.7, 0.5, 1.0) * 3.0, rr),tex(uv * 2.0 * max(0.0, t), 0.27 + (2.0 * rr)));

				}

				col = float3( col.r * 0.9, 0.12, col.b * 0.3 );
				
				return float4(col, SampleImageSprite(Texture,Input.UV0).a);
			}
		]]
	}
	MainCode PS_Sparks
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/wl2Gzc
			//Shader License: CC BY 3.0
			//Author: Jan Mróz (jaszunio15)

			// ********************

			// Sparks moving right-to-left
			#define MOVEMENT_DIRECTION float2(1.0, -0.7)
			#define PARTICLE_SCALE (float2(1.6, 0.5))
			#define PARTICLE_SCALE_VAR (float2(0.2, 0.25))
			#define PARTICLE_BLOOM_SCALE (float2(0.8, 0.5))
			#define PARTICLE_BLOOM_SCALE_VAR (float2(0.1, 0.3))

			// Sparks moving left-to-right
			//#define MOVEMENT_DIRECTION float2(-1.0, -0.7)
			//#define PARTICLE_SCALE (float2(0.5, 1.6))
			//#define PARTICLE_SCALE_VAR (float2(0.25, 0.2))
			//#define PARTICLE_BLOOM_SCALE (float2(0.5, 0.8))
			//#define PARTICLE_BLOOM_SCALE_VAR (float2(0.3, 0.1))

			// ********************

			#define TWO_PI 6.283185

			#define ANIMATION_SPEED 1.5
			#define MOVEMENT_SPEED 0.7

			#define PARTICLE_SIZE 0.005

			#ifdef BALEFIRE
				#define SPARK_COLOR float3(0.5, 1.0, 0.05) * 1.5
				#define BLOOM_COLOR float3(0.2, 1.0, 0.05) * 0.8
				#define SMOKE_COLOR float3(0.7, 0.8, 0.5) * 1.0
			#else
				#define SPARK_COLOR float3(1.0, 0.4, 0.05) * 1.5
				#define BLOOM_COLOR float3(1.0, 0.4, 0.05) * 0.8
				#define SMOKE_COLOR float3(0.8, 0.7, 0.7) * 1.0
			#endif

			#define SIZE_MOD 1.08
			#define ALPHA_MOD 0.9
			#define LAYERS_COUNT 15

			float hash1_2(in float2 x)
			{
				float d = dot(x, float2(52.127, 61.2871));
				return frac(sin(d) * 521.582);   
			}

			float2 hash2_2(in float2 x)
			{
				float2 m = mul(x, float2x2(20.52, 24.1994, 70.291, 80.171));
				float2 s = float2(sin(m.x),sin(m.y));
				return frac(s * 492.194);
			}

			//Simple interpolated noise
			float2 noise2_2(float2 uv)
			{
				//float2 f = frac(uv);
				float2 f = smoothstep(0.0, 1.0, frac(uv));
				
				float2 uv00 = floor(uv);
				float2 uv01 = uv00 + float2(0,1);
				float2 uv10 = uv00 + float2(1,0);
				float2 uv11 = uv00 + 1.0;
				float2 v00 = hash2_2(uv00);
				float2 v01 = hash2_2(uv01);
				float2 v10 = hash2_2(uv10);
				float2 v11 = hash2_2(uv11);
				
				float2 v0 = lerp(v00, v01, f.y);
				float2 v1 = lerp(v10, v11, f.y);
				float2 v = lerp(v0, v1, f.x);
				
				return v;
			}

			//Simple interpolated noise
			float noise1_2(in float2 uv)
			{
				float2 f = frac(uv);
				//float2 f = smoothstep(0.0, 1.0, frac(uv));
				
				float2 uv00 = floor(uv);
				float2 uv01 = uv00 + float2(0,1);
				float2 uv10 = uv00 + float2(1,0);
				float2 uv11 = uv00 + 1.0;
				
				float v00 = hash1_2(uv00);
				float v01 = hash1_2(uv01);
				float v10 = hash1_2(uv10);
				float v11 = hash1_2(uv11);
				
				float v0 = lerp(v00, v01, f.y);
				float v1 = lerp(v10, v11, f.y);
				float v = lerp(v0, v1, f.x);
				
				return v;
			}

			float layeredNoise1_2(in float2 uv, in float sizeMod, in float alphaMod, in int layers, in float animation)
			{
				float noise = 0.0;
				float alpha = 1.0;
				float size = 1.0;
				float2 offset;
				for (int i = 0; i < layers; i++)
				{
					offset += hash2_2(float2(alpha, size)) * 10.0;
					
					//Adding noise with movement
					noise += noise1_2(uv * size + GuiTime * animation * 8.0 * MOVEMENT_DIRECTION * MOVEMENT_SPEED + offset) * alpha;
					alpha *= alphaMod;
					size *= sizeMod;
				}
				
				noise *= (1.0 - alphaMod)/(1.0 - pow(alphaMod, float(layers)));
				return noise;
			}

			//Rotates point around 0,0
			float2 rotate(in float2 coord, in float deg)
			{
				float s = sin(deg);
				float c = cos(deg);
				return mul(float2x2(s, c, -c, s), coord);
			}

			//Cell center from point on the grid
			float2 voronoiPointFromRoot(in float2 root, in float deg)
			{
				float2 coord = hash2_2(root) - 0.5;
				float s = sin(deg);
				float c = cos(deg);
				coord = mul(float2x2(s, c, -c, s), coord) * 0.66;
				coord += root + 0.5;
				return coord;
			}

			//Voronoi cell point rotation degrees
			float degFromRootUV(in float2 uv)
			{
				return GuiTime * ANIMATION_SPEED * (hash1_2(uv) - 0.5) * 2.0;   
			}

			float2 randomAround2_2(in float2 coord, in float2 range, in float2 uv)
			{
				return coord + (hash2_2(uv) - 0.5) * range;
			}


			float3 fireParticles(in float2 uv, in float2 originalUV)
			{
				float3 particles = float3(0.0,0.0,0.0);
				float2 rootUV = floor(uv);
				float deg = degFromRootUV(rootUV);
				float2 pointUV = voronoiPointFromRoot(rootUV, deg);
				float dist = 2.0;
				float distBloom = 0.0;
			
				//UV manipulation for the faster particle movement
				float2 tempUV = uv + (noise2_2(uv * 2.0) - 0.5) * 0.1;
				tempUV += -(noise2_2(uv * 3.0 + GuiTime) - 0.5) * 0.07;

				//Sparks sdf
				dist = length(rotate(tempUV - pointUV, 0.7) * randomAround2_2(PARTICLE_SCALE, PARTICLE_SCALE_VAR, rootUV));
				
				//Bloom sdf
				distBloom = length(rotate(tempUV - pointUV, 0.7) * randomAround2_2(PARTICLE_BLOOM_SCALE, PARTICLE_BLOOM_SCALE_VAR, rootUV));

				//Add sparks
				particles += (1.0 - smoothstep(PARTICLE_SIZE * 0.6, PARTICLE_SIZE * 3.0, dist)) * SPARK_COLOR;
				
				//Add bloom
				particles += pow((1.0 - smoothstep(0.0, PARTICLE_SIZE * 6.0, distBloom)) * 1.0, 3.0) * BLOOM_COLOR;

				//Upper disappear curve randomization
				float border = (hash1_2(rootUV) - 0.5) * 2.0;
				float disappear = 1.0 - smoothstep(border, border + 0.5, originalUV.y);
				
				//Lower appear curve randomization
				border = (hash1_2(rootUV + 0.214) - 1.8) * 0.7;
				float appear = smoothstep(border, border + 0.4, originalUV.y);
				
				return particles * disappear * appear;
			}


			//Layering particles to imitate 3D view
			float3 layeredParticles(in float2 uv, in float sizeMod, in float alphaMod, in int layers, in float smoke) 
			{ 
				float3 particles = float3(0.0,0.0,0.0);
				float size = 1.0;
				float alpha = 1.0;
				float2 offset = float2(0.0,0.0);
				float2 noiseOffset;
				float2 bokehUV;
				
				for (int i = 0; i < layers; i++)
				{
					//Particle noise movement
					noiseOffset = (noise2_2(uv * size * 2.0 + 0.5) - 0.5) * 0.15;
					
					//UV with applied movement
					bokehUV = (uv * size + GuiTime * MOVEMENT_DIRECTION * MOVEMENT_SPEED) + offset + noiseOffset; 
					
					//Adding particles								if there is more smoke, remove smaller particles
					particles += fireParticles(bokehUV, uv) * alpha * (1.0 - smoothstep(0.0, 1.0, smoke) * (float(i) / float(layers)));
					
					//Moving uv origin to avoid generating the same particles
					offset += hash2_2(float2(alpha, alpha)) * 10.0;
					
					alpha *= alphaMod;
					size *= sizeMod;
				}
				
				return particles;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;

				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv = float2(uv.x,0.5-uv.y);

				uv.x *= TextureSize.x / TextureSize.y;
				
				//float vignette = 1.0 - smoothstep(0.4, 1.4, length(uv + float2(0.0, 0.3)));
				
				uv *= 1.8;
				
				float smokeIntensity = layeredNoise1_2(uv * 10.0 + GuiTime * 4.0 * MOVEMENT_DIRECTION * MOVEMENT_SPEED, 1.7, 0.7, 6, 0.2);
				smokeIntensity *= pow(1.0 - smoothstep(-1.0, 1.6, uv.y), 2.0); 
				float3 smoke = smokeIntensity * SMOKE_COLOR * 0.8;
				//float3 smoke = smokeIntensity * SMOKE_COLOR * 0.8 * vignette;
				
				//Cutting holes in smoke
				smoke *= pow(layeredNoise1_2(uv * 4.0 + GuiTime * 0.5 * MOVEMENT_DIRECTION * MOVEMENT_SPEED, 1.8, 0.5, 3, 0.2), 2.0) * 1.5;
				
				float3 particles = layeredParticles(uv, SIZE_MOD, ALPHA_MOD, LAYERS_COUNT, smokeIntensity);
				
				float3 col = particles + smoke + SMOKE_COLOR * 0.02;
				//col *= vignette;
				
				col = smoothstep(-0.08, 1.0, col);

				#ifdef BALEFIRE
					float alpha = SampleImageSprite(Texture,Input.UV0).a * col.g;
				#else
					float alpha = SampleImageSprite(Texture,Input.UV0).a * col.r;
				#endif

				return float4(col, alpha);
			}
		]]
	}
	MainCode PS_Fire
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/MlKSWm

			//
			// Description : Array and textureless GLSL 2D/3D/4D simplex 
			//							 noise functions.
			//			Author : Ian McEwan, Ashima Arts.
			//	Maintainer : ijm
			//		 Lastmod : 20110822 (ijm)
			//		 License : Copyright (C) 2011 Ashima Arts. All rights reserved.
			//							 Distributed under the MIT License. See LICENSE file.
			//							 https://github.com/ashima/webgl-noise
			// 
 
			#define SPEED 0.7

			#define CLIP 410.0
			#define XFUELPOW 0.5
			#define FLAMESMOD1 0.3
			#define FLAMESMOD2 0.3

			float3 mod289(float3 x) {
				return x - floor(x * (1.0 / 289.0)) * 289.0;
			}

			float4 mod289(float4 x) {
				return x - floor(x * (1.0 / 289.0)) * 289.0;
			}

			float4 permute(float4 x) {
					return mod289(((x*34.0)+1.0)*x);
			}

			float4 taylorInvSqrt(float4 r)
			{
				return 1.79284291400159 - 0.85373472095314 * r;
			}

			float snoise(float3 v)
				{ 
				const float2	C = float2(1.0/6.0, 1.0/3.0) ;
				const float4	D = float4(0.0, 0.5, 1.0, 2.0);

			// First corner
				float3 i	= floor(v + dot(v, C.yyy) );
				float3 x0 	=	 v - i + dot(i, C.xxx) ;

			// Other corners
				float3 g = step(x0.yzx, x0.xyz);
				float3 l = 1.0 - g;
				float3 i1 = min( g.xyz, l.zxy );
				float3 i2 = max( g.xyz, l.zxy );

				//	 x0 = x0 - 0.0 + 0.0 * C.xxx;
				//	 x1 = x0 - i1	+ 1.0 * C.xxx;
				//	 x2 = x0 - i2	+ 2.0 * C.xxx;
				//	 x3 = x0 - 1.0 + 3.0 * C.xxx;
				float3 x1 = x0 - i1 + C.xxx;
				float3 x2 = x0 - i2 + C.yyy; // 2.0*C.x = 1/3 = C.y
				float3 x3 = x0 - D.yyy;			// -1.0+3.0*C.x = -0.5 = -D.y

			// Permutations
				i = mod289(i); 
				float4 p = permute( permute( permute( 
									i.z + float4(0.0, i1.z, i2.z, 1.0 ))
								+ i.y + float4(0.0, i1.y, i2.y, 1.0 )) 
								+ i.x + float4(0.0, i1.x, i2.x, 1.0 ));

			// Gradients: 7x7 points over a square, mapped onto an octahedron.
			// The ring size 17*17 = 289 is close to a multiple of 49 (49*6 = 294)
				float n_ = 0.142857142857; // 1.0/7.0
				float3	ns = n_ * D.wyz - D.xzx;

				float4 j = p - 49.0 * floor(p * ns.z * ns.z);	//	mod(p,7*7)

				float4 x_ = floor(j * ns.z);
				float4 y_ = floor(j - 7.0 * x_ );		// mod(j,N)

				float4 x = x_ *ns.x + ns.yyyy;
				float4 y = y_ *ns.x + ns.yyyy;
				float4 h = 1.0 - abs(x) - abs(y);

				float4 b0 = float4( x.xy, y.xy );
				float4 b1 = float4( x.zw, y.zw );

				//float4 s0 = float4(lessThan(b0,0.0))*2.0 - 1.0;
				//float4 s1 = float4(lessThan(b1,0.0))*2.0 - 1.0;
				float4 s0 = floor(b0)*2.0 + 1.0;
				float4 s1 = floor(b1)*2.0 + 1.0;
				float4 sh = -step(h, float4(0.0,0.0,0.0,0.0));

				float4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
				float4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;

				float3 p0 = float3(a0.xy,h.x);
				float3 p1 = float3(a0.zw,h.y);
				float3 p2 = float3(a1.xy,h.z);
				float3 p3 = float3(a1.zw,h.w);

			//Normalise gradients
				//float4 norm = taylorInvSqrt(float4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
				float4 norm = rsqrt(float4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
				p0 *= norm.x;
				p1 *= norm.y;
				p2 *= norm.z;
				p3 *= norm.w;

			// Mix final noise value
				float4 m = max(0.6 - float4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
				m = m * m;
				return 42.0 * dot( m*m, float4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );
				}

			//////////////////////////////////////////////////////////////

			// PRNG
			// From https://www.shadertoy.com/view/4djSRW
			float prng(in float2 seed) {
				seed = frac(seed * float2 (5.3983, 5.4427));
				seed += dot (seed.yx, seed.xy + float2 (21.5351, 14.3137));
				return frac(seed.x * seed.y * 95.4337);
			}

			//////////////////////////////////////////////////////////////

			float noiseStack(float3 pos,int octaves,float falloff){
				float noise = snoise(float3(pos));
				float off = 1.0;
				if (octaves>1) {
					pos *= 2.0;
					off *= falloff;
					noise = (1.0-off)*noise + off*snoise(float3(pos));
				}
				if (octaves>2) {
					pos *= 2.0;
					off *= falloff;
					noise = (1.0-off)*noise + off*snoise(float3(pos));
				}
				if (octaves>3) {
					pos *= 2.0;
					off *= falloff;
					noise = (1.0-off)*noise + off*snoise(float3(pos));
				}
				return (1.0+noise)/2.0;
			}

			float2 noiseStackUV(float3 pos,int octaves,float falloff,float diff){
				float displaceA = noiseStack(pos,octaves,falloff);
				float displaceB = noiseStack(pos+float3(3984.293,423.21,5235.19),octaves,falloff);
				return float2(displaceA,displaceB);
			}

			PDX_MAIN
			{
				float time = GuiTime;
				float2 uv = Input.UV0;
				uv.y = 1.0 - uv.y;

				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);
				
				//uv.x *= 0.95;
				//uv.x *= TextureSize.x / TextureSize.y;

				float2 fragPosition = uv * TextureSize;
				//
				float xpart = uv.x;
				float ypart = uv.y;
				//
				float clip = CLIP;
				//float clip = 210.0;
				float ypartClip = fragPosition.y/clip;
				float ypartClippedFalloff = clamp(2.0-ypartClip,0.0,1.0);
				float ypartClipped = min(ypartClip,1.0);
				float ypartClippedn = 1.0-ypartClipped;
				//
				float xfuel = pow(xpart+0.2,XFUELPOW);
				//float xfuel = pow(1.5-abs(2.0*xpart-1.0),XFUELPOW);
				//float xfuel = pow(1.0-abs(2.0*xpart-1.0),XFUELPOW);
				//float xfuel = 1.0-abs(2.0*xpart-1.0);//pow(1.0-abs(2.0*xpart-1.0),0.5);
				//
				float timeSpeed = SPEED;
				float realTime = timeSpeed*time;
				//
				float2 coordScaled = 0.01*fragPosition;
				float3 position = float3(coordScaled,0.0);
				//float3 position = float3(coordScaled,0.0) + float3(1223.0,6434.0,8425.0);
				float3 flow = float3(4.1*(0.5-xpart)*pow(ypartClippedn,4.0),-2.0*xfuel*pow(ypartClippedn,64.0),0.0);
				float3 timing = realTime*float3(0.0,-1.7,1.1) + flow;
				//
				float3 displacePos = float3(1.0,0.5,1.0)*2.4*position+realTime*float3(0.01,-0.7,1.3);
				float3 displace3 = float3(noiseStackUV(displacePos,2,0.4,0.1),0.0);
				//
				float3 noiseCoord = (float3(2.0,1.0,1.0)*position+timing+0.4*displace3)/1.0;
				float noise = noiseStack(noiseCoord,3,0.4);
				//
				float flames = pow(ypartClipped,FLAMESMOD1*xfuel)*pow(noise,FLAMESMOD2*xfuel);
				//
				float f = ypartClippedFalloff*pow(1.0-flames*flames*flames,8.0);
				float fff = f*f*f;
				#ifdef BALEFIRE
					float3 fire = 1.5*float3(pow(f,1.7), f, fff*fff);
				#else
					float3 fire = 1.5*float3(f, fff, fff*fff);
				#endif
				//
				// smoke
				float smokeNoise = 0.5+snoise(0.4*position+timing*float3(1.0,1.0,0.2))/2.0;
				float smokeScalar = 0.3*pow(xfuel,3.0)*pow(ypart,2.0)*(smokeNoise+0.4*(1.0-noise));
				float3 smoke = float3(smokeScalar,smokeScalar,smokeScalar);
				//
				// sparks
				float sparkGridSize = 30.0;
				float2 sparkCoord = fragPosition;
				sparkCoord -= 30.0*noiseStackUV(0.01*float3(sparkCoord,30.0*time),1,0.4,0.1);
				sparkCoord += 100.0*flow.xy;
				if (mod(sparkCoord.y/sparkGridSize,2.0)<1.0) sparkCoord.x += 0.5*sparkGridSize;
				float2 sparkGridIndex = float2(floor(sparkCoord/sparkGridSize));
				float sparkRandom = prng(sparkGridIndex);
				float sparkLife = min(10.0*(1.0-min((sparkGridIndex.y+(190.0*realTime/sparkGridSize))/(24.0-20.0*sparkRandom),1.0)),1.0);
				float3 sparks = float3(0.0,0.0,0.0);
				if (sparkLife>0.0) {
					float sparkSize = xfuel*xfuel*sparkRandom*0.08;
					float sparkRadians = 999.0*sparkRandom*2.0*PI + 2.0*time;
					float2 sparkCircular = float2(sin(sparkRadians),cos(sparkRadians));
					float2 sparkOffset = (0.5-sparkSize)*sparkGridSize*sparkCircular;
					float2 sparkModulus = mod(sparkCoord+sparkOffset,sparkGridSize) - 0.5*float2(sparkGridSize,sparkGridSize);
					float sparkLength = length(sparkModulus);
					float sparksGray = max(0.0, 1.0 - sparkLength/(sparkSize*sparkGridSize));
					#ifdef BALEFIRE
						sparks = sparkLife*sparksGray*float3(0.7,1.0,0.0);
					#else
						sparks = sparkLife*sparksGray*float3(1.0,0.3,0.0);
					#endif
				}
				//
				float3 color = max(fire,sparks) + smoke;
				#ifdef BALEFIRE
					float alpha = SampleImageSprite(Texture,Input.UV0).a * color.g;
				#else
					float alpha = SampleImageSprite(Texture,Input.UV0).a * color.r;
				#endif
				return float4(color, alpha);
			}
		]]
	}
	MainCode PS_Fog
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/7tsfWS
			
			float rand(float2 n) {
				return frac(cos(dot(n, float2(12.9898, 4.1414))) * 43758.5453);
			}

			float noise(float2 n) {
				const float2 d = float2(0.0, 1.0);
				float2 b = floor(n), f = smoothstep(float2(0.0,0.0), float2(1.0,1.0), frac(n));
				return lerp(lerp(rand(b), rand(b + d.yx), f.x), lerp(rand(b + d.xy), rand(b + d.yy), f.x), f.y);
			}

			float fbm(float2 n) {
				float total = 0.0, amplitude = 1.0;
				for (int i = 0; i < 4; i++) {
					total += noise(n) * amplitude;
					n += n;
					amplitude *= 0.5;
				}
				return total;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				uv.y = 1.0 - uv.y;

				#if defined(HEIST_MAP)
					float2 TextureSize = float2(1300.0, 600.0);
					float2 coord = float2(uv.x * TextureSize.x, uv.y * TextureSize.y);
				#elif defined(SUSPICION_BUTTON)
					float2 TextureSize = float2(500.0, 105.0);
					float2 coord = float2(uv.x * TextureSize.x, uv.y * TextureSize.y);
				#else
					float2 TextureSize;
					PdxTex2DSize(Texture, TextureSize);

					float2 coord = float2(uv.x * TextureSize.x, uv.y * TextureSize.y);
					coord.x *= TextureSize.x / TextureSize.y;
				#endif

				#if defined(SUSPICION1)
					float time = GuiTime * 0.5;
				#elif defined(SUSPICION2)
					float time = GuiTime * 0.7;
				#elif defined(SUSPICION3)
					float time = GuiTime * 0.9;
				#elif defined(SUSPICION4)
					float time = GuiTime * 1.1;
				#else
					float time = GuiTime * 1.0;
				#endif

				//const float3 c1 = float3(124.0/255.0, 0.0/255.0, 97.0/255.0);
				//const float3 c2 = float3(173.0/255.0, 0.0/255.0, 161.4/255.0);
				//const float3 c3 = float3(0.2, 0.0, 0.0);
				//const float3 c4 = float3(164.0/255.0, 1.0/255.0, 214.4/255.0);
				//const float3 c5 = float3(0.1, 0.1, 0.1);
				//const float3 c6 = float3(0.9, 0.9, 0.9);

				#if defined(SUSPICION2)
					const float3 c1 = float3(30.0/255.0, 40.0/255.0, 50.0/255.0);
					const float3 c2 = float3(130.0/255.0, 140.0/255.0, 155.0/255.0);
					const float3 c4 = float3(120.0/255.0, 130.0/255.0, 140.0/255.0);
				#elif defined(SUSPICION3)
					const float3 c1 = float3(50.0/255.0, 40.0/255.0, 10.0/255.0);
					const float3 c2 = float3(170.0/255.0, 140.0/255.0, 60.0/255.0);
					const float3 c4 = float3(150.0/255.0, 120.0/255.0, 20.0/255.0);
				#elif defined(SUSPICION4)
					const float3 c1 = float3(50.0/255.0, 0.0/255.0, 50.0/255.0);
					const float3 c2 = float3(200.0/255.0, 100.0/255.0, 0.0/255.0);
					const float3 c4 = float3(170.0/255.0, 60.0/255.0, 0.0/255.0);
				#else
					const float3 c1 = float3(0.0/255.0, 50.0/255.0, 50.0/255.0);
					const float3 c2 = float3(0.0/255.0, 140.0/255.0, 173.0/255.0);
					const float3 c4 = float3(0.0/255.0, 120.0/255.0, 160.0/255.0);
				#endif
				
				const float3 c3 = float3(0.2, 0.2, 0.2);
				const float3 c5 = float3(0.1, 0.1, 0.1);
				const float3 c6 = float3(0.9, 0.9, 0.9);

				float2 speed = float2(0.1, 0.4);
				float shift = 1.6;
				float2 p = coord.xy * 8.0 / TextureSize.xx;
				float q = fbm(p - time * 0.1);
				float2 r = float2(fbm(p + q + time * speed.x - p.x - p.y), fbm(p + q - time * speed.y));
				float3 c = lerp(c1, c2, fbm(p + r)) + lerp(c3, c4, r.x) - lerp(c5, c6, r.y);
				float grad = uv.y;

				float3 col = c * cos(shift * uv.y);
				//col *= 1.0-grad;

				#if defined(SUSPICION3)
					float alpha = SampleImageSprite(Texture,Input.UV0).a * col.r;
				#elif defined(SUSPICION4)
					float alpha = SampleImageSprite(Texture,Input.UV0).a * col.r;
				#else
					float alpha = SampleImageSprite(Texture,Input.UV0).a * col.b;
				#endif

				alpha *= 1.0-grad;
				alpha *= 0.7;
				return float4(col,alpha);
			}
		]]
	}
	MainCode PS_Hypertrip
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/4tX3Rf
			
			// Particles + Noise Part 2
			// By: Brandon Fogerty
			// bfogerty at gmail dot com


			#define Time					GuiTime

			#define HorizontalAmplitude		0.50
			#define VerticleAmplitude		0.50
			#define HorizontalSpeed			0.90
			#define VerticleSpeed			0.30
			#define ParticleMinSize			1.76
			#define ParticleMaxSize			1.61
			#define ParticleBreathingSpeed		0.10
			#define ParticleColorChangeSpeed	0.70
			#define ParticleCount			2.0
			#define ParticleColor1			float3(1.5, 0.0, 0.5)
			#define ParticleColor2			float3(1.5, 0.5, 0.0)


			float hash( float x )
			{
				return frac( sin( x ) * 43758.5453 );
			}

			float noise( float2 uv )  // Thanks Inigo Quilez
			{
				float3 x = float3( uv.xy, 0.0 );
				
				float3 p = floor( x );
				float3 f = frac( x );
				
				f = f*f*(3.0 - 2.0*f);
				
				float offset = 57.0;
				
				float n = dot( p, float3(1.0, offset, offset*2.0) );
				
				return lerp(lerp(	lerp( hash( n + 0.0 ), 	 	 hash( n + 1.0 ), f.x ),
									lerp( hash( n + offset), 	 hash( n + offset+1.0), f.x ), f.y ),
							lerp(	lerp( hash( n + offset*2.0), hash( n + offset*2.0+1.0), f.x),
									lerp( hash( n + offset*3.0), hash( n + offset*3.0+1.0), f.x), f.y), f.z);
			}

			float snoise( float2 uv )
			{
				return noise( uv ) * 2.0 - 1.0;
			}


			float perlinNoise( float2 uv )
			{   
				float n = 	noise( uv * 1.0 ) 	* 128.0 +
							noise( uv * 2.0 ) 	* 64.0 +
							noise( uv * 4.0 ) 	* 32.0 +
							noise( uv * 8.0 ) 	* 16.0 +
							noise( uv * 16.0 ) 	* 8.0 +
							noise( uv * 32.0 ) 	* 4.0 +
							noise( uv * 64.0 ) 	* 2.0 +
							noise( uv * 128.0 ) * 1.0;
				
				float noiseVal = n / ( 1.0 + 2.0 + 4.0 + 8.0 + 16.0 + 32.0 + 64.0 + 128.0 );
				noiseVal = abs(noiseVal * 2.0 - 1.0);
				
				return 	noiseVal;
			}

			float fBm( float2 uv, float lacunarity, float gain )
			{
				float sum = 0.0;
				float amp = 10.0;
				
				for( int i = 0; i < 2; ++i )
				{
					sum += ( perlinNoise( uv ) ) * amp;
					amp *= gain;
					uv *= lacunarity;
				}
				
				return sum;
			}

			float3 particles( float2 pos )
			{
				
				float3 c = float3( 0, 0, 0 );
				
				float noiseFactor = fBm( pos, 0.01, 0.1);
				
				for( float i = 1.0; i < ParticleCount+1.0; ++i )
				{
					float cs = cos( Time * HorizontalSpeed * (i/ParticleCount) + noiseFactor ) * HorizontalAmplitude;
					float ss = sin( Time * VerticleSpeed   * (i/ParticleCount) + noiseFactor ) * VerticleAmplitude;
					float2 origin = float2( cs , ss );
					
					float t = sin( Time * ParticleBreathingSpeed * i ) * 0.5 + 0.5;
					float particleSize = lerp( ParticleMinSize, ParticleMaxSize, t );
					float d = clamp( sin( length( pos - origin )  + particleSize ), 0.0, particleSize);
					
					float t2 = sin( Time * ParticleColorChangeSpeed * i ) * 0.5 + 0.5;
					float3 color = lerp( ParticleColor1, ParticleColor2, t2 );
					c += color * pow( d, 10.0 );
				}
				
				return c;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				uv.y = 1.0 - uv.y;
				
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				uv = uv * 2.0 - 1.0;
				uv.x *= TextureSize.x / TextureSize.y * 1.4;
				uv.x -= 0.8;

				float3 finalColor = particles( sin( abs(uv) ) );
				finalColor.r += (1.0-uv.y)*0.15;
				
				return float4( finalColor, SampleImageSprite(Texture,Input.UV0).a );
			}
		]]
	}
	MainCode PS_Flowyblood
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/ftd3zX
			
			float rand(float2 p) {
				return frac(sin(dot(p, float2(12.99, 78.233))) * 43758.545);
			}

			float noise(float2 p) {
				float2 f = frac(p);
				f = f * f * f * f * (3. - 2. * f) * (3. - 2. * f);
				float2 i = floor(p);
				return lerp(lerp(rand(i + float2(0, 0)), 
							rand(i + float2(1, 0)), f.x),
						lerp(rand(i + float2(0, 1)), 
							rand(i + float2(1, 1)), f.x), f.y);
			}

			float fbm(float2 p) {
				float v = 0.;
				float a = 1.;
				for(int i = 0; i < 4; ++i) {
					p = 1.5 * p + 15.;
					a *= 0.5;
					v += a * noise(p);
				}
				return v;
			}

			PDX_MAIN
			{
				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				float2 uv = Input.UV0;
				uv.x = 1.0 - uv.x;
				uv.x *= 1.6;
				float2 p = 3.5 * uv;

				float time = GuiTime * 2.5;
				
				float2 r1 = float2(fbm(p + 0.02 * time), fbm(p + 0.005 * time));
				float2 r2 = float2(fbm(p + 0.15 * time + 10. * r1), fbm(p + 0.12 * time + 12. * r1));

				float col = 1.8 * pow(fbm(p + r2), 2.) + 0.03;

				#if defined(GOLD)
					float3 finalColor = float3(col, pow(col, 1.8)*0.9, col*col*col*col*col*0.25);
				#elif defined(GREY)
					float3 finalColor = float3(col*0.4, col*0.45, col*0.5);
				#elif defined(RITUALGREEN)
					float3 finalColor = float3(col*col*0.4, col*0.9, col*col);
				#elif defined(SORCERY)
					float3 finalColor = float3(col*col*0.4, col*0.9, col*col);
				#else
					float3 finalColor = float3(col, 0.0, col*col*col*col*col*0.25);
				#endif

				float alpha = SampleImageSprite(Texture,Input.UV0).a * col * 1.2;

				return float4( finalColor, alpha );
			}
		]]
	}
	MainCode PS_DeepUmbra
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/Mll3zj
			
			// Star Nest by Pablo RomÃ¡n Andrioli

			// This content is under the MIT License.

			// Original post by Kali https://www.shadertoy.com/view/XlfGRj

			#define iterations 17
			#define formuparam 0.53

			#define volsteps 20
			#define stepsize 0.1

			#define zoom   0.800
			#define tile   0.850
			#define speed  0.004

			#define brightness 0.0016
			#define darkmatter 0.300
			#define distfading 0.750
			#define saturation 1.000

			float SCurve (float value) {

				if (value < 0.5)
				{
					return value * value * value * value * value * 16.0; 
				}
				
				value -= 1.0;
				
				return value * value * value * value * value * 16.0 + 1.0;
			}

			PDX_MAIN
			{
				float2 uv = Input.UV0;
				//uv = float2(1.0,1.0) - uv;
				uv.x = 1.0 - uv.x;

				float2 TextureSize;
				PdxTex2DSize(Texture, TextureSize);

				//get coords and direction
				uv = uv - 0.5;
				uv.y *= TextureSize.y/TextureSize.x;
				#ifdef EVENT
				uv.x *= 1.4;
				#endif
				float3 dir=float3(uv*zoom,1.);
				float time=GuiTime*speed+.25;

				//mouse rotation (mouse input disabled for POD)
				float a1=.5+1.0/TextureSize.x*2.;
				float a2=.8+1.0/TextureSize.y*2.;
				float2x2 rot1=float2x2(cos(a1),sin(a1),-sin(a1),cos(a1));
				float2x2 rot2=float2x2(cos(a2),sin(a2),-sin(a2),cos(a2));
				dir.xz=mul(dir.xz,rot1);
				dir.xy=mul(dir.xy,rot2);
				float3 from=float3(1.,.5,0.5);
				from+=float3(time*2.,time,-2.);
				from.xz=mul(from.xz,rot1);
				from.xy=mul(from.xy,rot2);
				//disappearing stars (happy accident?)
				//from.xz*=mul(from.xz,rot1);
				//from.xy*=mul(from.xy,rot2);
				
				//volumetric rendering
				float s=0.1,fade=1.;
				float3 v=float3(0.,0.,0.);
				for (int r=0; r<volsteps; r++) {
					float3 p=from+s*dir*.5;
					p = abs(float3(tile,tile,tile)-mod(p,float3(tile*2.,tile*2.,tile*2.))); // tiling fold
					float pa,a=pa=0.;
					for (int i=0; i<iterations; i++) { 
						p=abs(p)/dot(p,p)-formuparam; // the magic formula
						a+=abs(length(p)-pa); // absolute sum of average change
						pa=length(p);
					}
					float dm=max(0.,darkmatter-a*a*.001); //dark matter
					a = pow(a, 2.5); // add contrast
					if (r>6) fade*=1.-dm; // dark matter, don't render near
					//v+=float3(dm,dm*.5,0.);
					v+=fade;
					v+=float3(s,s*s,s*s*s*s)*a*brightness*fade; // coloring based on distance
					fade*=distfading; // distance fading
					s+=stepsize;
				}
				
				v=lerp(float3(length(v),length(v),length(v)),v,saturation); //color adjust
				
				float4 C = float4(v*.01,1.);
				
					C.r = pow(C.r, 0.35); 
					C.g = pow(C.g, 0.36); 
					C.b = pow(C.b, 0.4); 
				
				float4 L = C;   	
				
					C.r = lerp(L.r, SCurve(C.r), 1.0); 
					C.g = lerp(L.g, SCurve(C.g), 0.9); 
					C.b = lerp(L.b, SCurve(C.b), 0.6);     	
				
				float alpha = SampleImageSprite(Texture,Input.UV0).a;

				//vignette
				#ifndef EVENT
				float vig = 1.0-length(uv);
				C.rgb = lerp(C.rgb,C.rgb*float3(vig,vig,vig),0.8);
				alpha = lerp(alpha,alpha*vig,0.6);
				#endif
				return float4(C.rgb, alpha);
			}
		]]
	}
}

# SampleImageSprite( Texture, Input.UV0 );

BlendState BlendState
{
	BlendEnable = yes
	SourceBlend = "SRC_ALPHA"
	DestBlend = "INV_SRC_ALPHA"
}

BlendState BlendStateNoAlpha
{
	BlendEnable = no
}

BlendState PreMultipliedAlpha
{
	BlendEnable = yes
	SourceBlend = "ONE"
	DestBlend = "INV_SRC_ALPHA"
}

DepthStencilState DepthStencilState
{
	DepthEnable = no
}

Effect PdxGuiDefault
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
}
Effect PdxGuiDefaultDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	
	Defines = { "DISABLED" }
}

Effect PdxGuiDefaultNoAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = BlendStateNoAlpha
}
Effect PdxGuiDefaultNoAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = BlendStateNoAlpha
	
	Defines = { "DISABLED" }
}

Effect PdxGuiPreMultipliedAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = PreMultipliedAlpha
}
Effect PdxGuiPreMultipliedAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Default"
	BlendState = PreMultipliedAlpha
	
	Defines = { "DISABLED" }
}

Effect EventBackground
{
	VertexShader = "VS_Default"
	PixelShader = "PS_EventBackground"
}
Effect EventBackgroundDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_EventBackground"
	
	Defines = { "DISABLED" }
}

Effect ColorDisplay
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
}
Effect ColorDisplayDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "DISABLED" }
}

Effect ColorDisplayRedGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "RED_GRADIENT" }
}
Effect ColorDisplayRedGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "RED_GRADIENT" "DISABLED" }
}

Effect ColorDisplayGreenGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "GREEN_GRADIENT" }
}
Effect ColorDisplayGreenGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "GREEN_GRADIENT" "DISABLED" }
}

Effect ColorDisplayBlueGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "BLUE_GRADIENT" }
}
Effect ColorDisplayBlueGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "BLUE_GRADIENT" "DISABLED" }
}

Effect ColorDisplayHueGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "HUE_GRADIENT" }
}
Effect ColorDisplayHueGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "HUE_GRADIENT" "DISABLED" }
}

Effect ColorDisplaySaturationGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "SATURATION_GRADIENT" }
}
Effect ColorDisplaySaturationGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "SATURATION_GRADIENT" "DISABLED" }
}

Effect ColorDisplayValueGradient
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "VALUE_GRADIENT" }
}
Effect ColorDisplayValueGradientDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_ColorDisplay"
	
	Defines = { "VALUE_GRADIENT" "DISABLED" }
}

Effect Unmoored
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Unmoored"
}
Effect UnmooredDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Unmoored"
	
	Defines = { "DISABLED" }
}

Effect Kaleidoscope
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Kaleidoscope"
}
Effect KaleidoscopeDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Kaleidoscope"
	
	Defines = { "DISABLED" }
}

Effect Sparks
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Sparks"
}
Effect SparksDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Sparks"
	
	Defines = { "DISABLED" }
}

Effect BalefireSparks
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Sparks"
	
	Defines = { "BALEFIRE" }
}
Effect BalefireSparksDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Sparks"
	
	Defines = { "BALEFIRE" "DISABLED" }
}

Effect Fire
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fire"
}
Effect FireDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fire"
	
	Defines = { "DISABLED" }
}

Effect Balefire
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fire"
	
	Defines = { "BALEFIRE" }
}
Effect BalefireDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fire"
	
	Defines = { "BALEFIRE" "DISABLED" }
}

Effect Fog
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
}
Effect FogDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "DISABLED" }
}

Effect FogHeist1
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION1" }
}
Effect FogHeist1Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION1" "DISABLED" }
}

Effect FogHeist2
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION2" }
}
Effect FogHeist2Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION2" "DISABLED" }
}

Effect FogHeist3
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION3" }
}
Effect FogHeist3Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION3" "DISABLED" }
}

Effect FogHeist4
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION4" }
}
Effect FogHeist4Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "HEIST_MAP" "SUSPICION4" "DISABLED" }
}

Effect FogSuspicion1
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION1" }
}
Effect FogSuspicion1Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION1" "DISABLED" }
}

Effect FogSuspicion2
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION2" }
}
Effect FogSuspicion2Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION2" "DISABLED" }
}

Effect FogSuspicion3
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION3" }
}
Effect FogSuspicion3Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION3" "DISABLED" }
}

Effect FogSuspicion4
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION4" }
}
Effect FogSuspicion4Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Fog"
	
	Defines = { "SUSPICION_BUTTON" "SUSPICION4" "DISABLED" }
}

Effect Hypertrip
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Hypertrip"
}
Effect HypertripDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Hypertrip"
	
	Defines = { "DISABLED" }
}

Effect FlowyBlood
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
}
Effect FlowyBloodDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "DISABLED" }
}

Effect FlowyGold
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "GOLD" }
}
Effect FlowyGoldDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "GOLD" "DISABLED" }
}

Effect FlowyGrey
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "GREY" }
}
Effect FlowyGreyDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "GREY" "DISABLED" }
}

Effect FlowyRitual
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "RITUALGREEN" }
}
Effect FlowyRitualDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "RITUALGREEN" "DISABLED" }
}

Effect FlowySorcery
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "SORCERY" }
}
Effect FlowySorceryDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_Flowyblood"
	
	Defines = { "SORCERY" "DISABLED" }
}

Effect DeepUmbra
{
	VertexShader = "VS_Default"
	PixelShader = "PS_DeepUmbra"
}
Effect DeepUmbraDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_DeepUmbra"
	
	Defines = { "DISABLED" }
}

Effect DeepUmbraEvent
{
	VertexShader = "VS_Default"
	PixelShader = "PS_DeepUmbra"
	
	Defines = { "EVENT" }
}
Effect DeepUmbraEventDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_DeepUmbra"
	
	Defines = { "EVENT" "DISABLED" }
}
