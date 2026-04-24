# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
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
	
	MainCode PS_PODFBM
	{	
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/7tsfWS
			
			// float rand(float2 n) {
			// 	return frac(cos(dot(n, float2(12.9898, 4.1414))) * 43758.5453);
			// }
			
			// hash without sine, by dave hoskins https://www.shadertoy.com/view/4djSRW
			// because the trig-based hash functions cause issues on vulkan
			float rand(float2 p) {
				float3 p3 = frac(float3(p.xyx) * .1031);
				p3 += dot(p3, p3.yzx + 33.33);
				return frac((p3.x + p3.y) * p3.z);
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

				float2 coord = uv * SpriteSize.xy;
				coord *= SpriteBorder[0].y; // spriteborder_top (zoom)
				coord.x *= SpriteSize.x / SpriteSize.y;
				coord.x *= SpriteBorder[0].z; // spriteborder_right (aspect ratio)

				float time = GuiTime * SpriteBorder[0].x; // spriteborder_left (speed)

				float3 c1 = SpriteModifyTexturesColors[1].rgb;
				float3 c2 = SpriteModifyTexturesColors[2].rgb;
				float3 c4 = SpriteModifyTexturesColors[3].rgb;
				
				const float3 c3 = float3(0.2, 0.2, 0.2);
				const float3 c5 = float3(0.1, 0.1, 0.1);
				const float3 c6 = float3(0.9, 0.9, 0.9);

				float2 speed = SpriteBorder[4].xy; // vertical/horizontal speed
				float shift = 1.6;
				float2 p = coord.xy * 8.0 / SpriteSize.xx;
				float q = fbm(p - time * 0.1);
				float2 r = float2(fbm(p + q + time * speed.x - p.x - p.y), fbm(p + q - time * speed.y));
				float3 c = lerp(c1, c2, fbm(p + r)) + lerp(c3, c4, r.x) - lerp(c5, c6, r.y);
				float grad = 1.0-uv.y;

				float3 col = c * cos(shift * uv.y);

				float alphaChannels = lerp( 1., col.r, SpriteModifyTexturesColors[4].r );
				alphaChannels *= lerp( 1., col.g, SpriteModifyTexturesColors[4].g );
				alphaChannels *= lerp( 1., col.b, SpriteModifyTexturesColors[4].b );
				
				float alpha = SampleImageSprite(Texture,Input.UV0).a * SpriteTranslateRotateUVAndAlpha[4].w * alphaChannels;

				alpha = lerp( alpha, alpha*grad, SpriteBorder[0].w ); // spriteborder_bottom (gradient strength)
				return float4(col,alpha);
			}
		]]
	}

	MainCode PS_PODTernaryGraph
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// hash without sine, by dave hoskins https://www.shadertoy.com/view/4djSRW
			// because the trig-based hash functions cause issues on vulkan
			float hash(float2 p) {
				float3 p3 = frac(float3(p.xyx) * .1031);
				p3 += dot(p3, p3.yzx + 33.33);
				return frac((p3.x + p3.y) * p3.z);
			}
			
			float noise(float2 p) {
				float2 ip = floor(p);
				float2 u = frac(p);
				u = u*u*(3.0-2.0*u);
				float res = lerp(
					lerp(hash(ip),hash(ip+float2(1.0,0.0)),u.x),
					lerp(hash(ip+float2(0.0,1.0)),hash(ip+float2(1.0,1.0)),u.x),u.y);
				return res*res;
			}
			
			float fbm( in float2 x, in float2 speed ) {
				const float H = 0.8;
				float G = exp2(-H);
				float f = 1.0;
				float a = 1.0;
				float t = 0.0;
				for( int i=0; i<12; i++ ) {
					t += a*noise(f * x + speed);
					f *= 2.0;
					a *= G;
				}
				//return t;
				return smoothstep(0.,1.5,t);
			}
			
			float domainwarp( in float2 p, in float2 speed ) {
				float2 q = float2( fbm( p + float2(0.0,0.0), speed ),
							fbm( p + float2(5.2,1.3), speed ) );

				return fbm( p + 4.0*q, speed );
			}
			
			// equilateral triangle SDF, from https://www.shadertoy.com/view/Xl2yDW
			// r is the bounding circle's radius
			float sdEquilateralTriangle( in float2 p, in float r ) {
				const float k = sqrt(3.0);
				p.x = abs(p.x);
				p -= float2(0.5,0.5*k)*max(p.x+k*p.y,0.0);
				p -= float2(clamp(p.x,-0.5*r*k,0.5*r*k),-0.5*r);
				return length(p)*sign(-p.y);
			}
			
			float2 rot2d(in float2 coord, in float angle) {
				float c = cos(angle);
				float s = sin(angle);
				return mul( coord, float2x2(c, -s, s, c) );
			}
			
			float SDFToLine( in float x, in float thickness, in float feathering ) {
				float min = thickness - feathering;
				float max = thickness + feathering;
				return smoothstep(max,min,x);
			}
			
			// because guess what, the modulo operator works differently in GLSL and HLSL
			// https://stackoverflow.com/questions/7610631/glsl-mod-vs-hlsl-fmod
			float GLSLmod(in float x, in float y) {
				return x - y * floor(x/y);
			}
			
			PDX_MAIN
			{
				float2 uv = Input.UV0;
				uv.y = 1.0 - uv.y; // UVs are upside down in ck3
				float2 fragCoord = uv * SpriteSize.xy;
				float2 p = (2.0*fragCoord.xy-SpriteSize.xy)/SpriteSize.y;
				
				// center (sort of) and zoom
				//p *= 0.75;
				//p.y += 0.25;
				//p *= 1.25;
				
				// alternatively, scoot a bit
				//p.y += 0.1;
				
				float grid_divisions    = SpriteBorder[0].x; // spriteborder_left
				float line_thickness    = SpriteBorder[0].y; // spriteborder_top
				float line_feathering   = SpriteBorder[0].z; // spriteborder_right
				float domainwarp_weight = SpriteBorder[0].w; // spriteborder_bottom
				
				float lineweight_gradient = SpriteBorder[1].x; // spriteborder_left
				
				
				// first domainwarp to un-straighten the lines
				p.x += (-0.5+0.5*domainwarp(p*0.2, 0.))*0.01*domainwarp_weight;
				p.y += (-0.5+0.5*domainwarp(p*0.2,10.))*0.01*domainwarp_weight;
				// second domainwarp to feather the lines ("pencil" texture)
				p.x += (-0.5+0.5*domainwarp(p*40.,20.))*0.008*domainwarp_weight;
				p.y += (-0.5+0.5*domainwarp(p*40.,30.))*0.008*domainwarp_weight;
				
				float sdf = sdEquilateralTriangle( p, 1.0 );
				
				float2 pa = rot2d(p, 2.0*PI*(1.0/3.0));
				float2 pb = rot2d(p, 2.0*PI*(2.0/3.0));
				
				float interval = 1.5 / grid_divisions;
				
				float lines_a = min( GLSLmod( pa.y-1.0, interval ), GLSLmod( -pa.y+1.0, interval ) );
				float lines_b = min( GLSLmod( pb.y-1.0, interval ), GLSLmod( -pb.y+1.0, interval ) );
				float lines_c = min( GLSLmod(  p.y-1.0, interval ), GLSLmod(  -p.y+1.0, interval ) );
				
				float grid = min(lines_a,min(lines_b,min(lines_c,-sdf)));
				
				// lines become thinner near the center
				float line_thickness_center = line_thickness * min( 0.35 + length(p*0.6), 1.0 );
				float line_thickness_grid = lerp(line_thickness, line_thickness_center, lineweight_gradient);
				
				float grid_ss     = SDFToLine( grid, line_thickness_grid, line_feathering );
				float bound_outer = SDFToLine(  sdf, line_thickness,      line_feathering );
				
				float alpha = lerp( 0.0, 1.0, grid_ss * bound_outer );
				
				float4 color = SpriteModifyTexturesColors[1];
				color.a *= alpha;
				color.a *= SampleImageSprite( Texture, Input.UV0 ).a; // apply modify_texture alphamultiply
				return color;
			}
		]]
	}

	MainCode PS_PODYomi
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/csS3zW
			
			// High Voltage Tendencies
			// Another cloud shader

			// reduces if too slow
			#define FRAMES 3.

			// snippets
			float2x2 rot (float a) { float c=cos(a),s=sin(a); return float2x2(c,-s,s,c); }
			float gyroid (float3 seed) { return dot(sin(seed),cos(seed.yzx)); }

			// noise
			float fbm (float3 seed)
			{
				float result = 0., a = .5;
				for (int i = 0; i < 8; ++i, a/=2.)
				{
					result += abs(gyroid(seed/a))*a;
				}
				return result;
			}

			// signed distance function
			float map(in float3 p, in float time, inout float glow)
			{
				float dist = 100.;
				
				// cloud
				float3 seed = p*.4;
				seed.z += time*.1;
				float noise = fbm(seed);
				dist = length(p) - .5 - noise*1.;
				
				// lightning
				const float count = 4.;
				float a = 1.;
				float t = time*.2 + time*.5;
				float r = .1+.2*sin(time+p.x);
				float shape = 100.;
				for (float i = 0.; i < count; ++i)
				{
					p.xz = mul(p.xz,rot(t/a));
					p.xy = mul(p.xy,rot(t/a));
					p = abs(p)-r*a;
					shape = min(shape, length(p.xz));
					a /= 1.8;
				}
				glow += .002/shape;
				//dist = min(dist, shape);
				
				return dist*.8;
			}

			PDX_MAIN
			{
				//float2 uv = Input.UV0;
				float2 fragCoord = Input.UV0 * SpriteSize.xy;
				
				float2 uv = (fragCoord-SpriteSize.xy/2.)/SpriteSize.y;
				// scoot for event images
				uv.x -= 0.4;
				float3 color = float3(0.,0.,0.);
				
				// layers
				for (float f = 0.; f < FRAMES; ++f)
				{
					// blue noise scroll by iq https://www.shadertoy.com/view/tlySzR
					//int2 p = int2(fragCoord);
					//p = (p+(int(GuiTime*60.)*196+int(f))*int2(113,127)) & 1023;
					//float2 puv = float2(float(p.x),float(p.y)) / 1024.;
					
					//float3 blu = PdxTex2D(ModifyTexture0, puv).rgb;
					//float3 blu = PdxReadBuffer3( ModifyTexture1, p );
					//float3 blu = texelFetch(iChannel0,p,0).xyz;
					float3 blu = float3(1.,1.,1.);

					// coordinates
					float3 pos = float3(0.,0.,7.);
					float3 ray = normalize(float3(uv,-3.));
					ray.xy += blu.xy * smoothstep(.5,8.,length(uv)); // blur edge
					pos += ray * blu.z * 4.; // pre start

					float3 tint = float3(0.,0.,0.);
					float glow = 0.;
					
					float time = GuiTime * 0.25; // TODO: set speed in shader

					// raymarch
					const float count = 40.;
					float maxDist = 10.;
					float steps = 0.;
					float total = 0.;
					for (steps = count; steps > 0.; --steps) {
						float dist = map(pos,time,glow);
						if (dist < .001*total || total > maxDist) break;
						dist *= 0.9+0.1*blu.z; // dithering
						ray.xy += blu.xy*total*.001; // depth of field
						pos += ray * dist;
						total += dist;
					}

					// shading
					float shade = steps/count;
					if (shade > .1 && total < maxDist) {

						// NuSan https://www.shadertoy.com/view/3sBGzV
						float2 noff = float2(.2*pow(length(uv),2.),0);
						float3 normal = normalize( map(pos,time,glow) - float3( map(pos-noff.xyy,time,glow),
						                                                        map(pos-noff.yxy,time,glow),
																		        map(pos-noff.yyx,time,glow) ) );

						// color palette https://iquilezles.org/www/articles/palettes/palettes.htm
						//tint = .8+.5*cos(float3(1,2,3)*6.1 + pos.y*1. + normal.z*3.);
						//tint += abs(pos.y) + normal.z + pos.z;
						tint += pos.z;

						// backlight
						tint *= dot(normal, ray)*.5+.5;
					}

					// bloom
					//tint += glow*.5;
					
					// average
					color += tint/FRAMES;
				}
				
				float3 col1 = SpriteModifyTexturesColors[1].rgb;
				float3 col2 = SpriteModifyTexturesColors[2].rgb;
				
				float3 outcol = lerp(col1,col2,color.r);
				
				float alpha = SampleImageSprite( Texture, Input.UV0 ).a;
				return float4(outcol, alpha);
			}
		]]
	}

	MainCode PS_PODVeins
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			#define TAO 6.2831853
			#define S smoothstep
			#define SPEED 0.1
			
			float2 R(float2 u, float a) { return mul(float2x2(cos(a), sin(a), -sin(a), cos(a)), u); }
			
			float N(float2 uv, float t, float p) {
				float2 a = float2(0.,0.), res = float2(0.,0.);
				float s = 10.;
				for (int j = 0; j < 30; j++) {
					uv = R(uv, 1.);
					a = R(a, 1.);
					float2 L = uv * s + float(j) + a - t;
					a += cos(L);
					res += (.5 + .5 * sin(L)) / s;
					s *= (1.2 - .07 * p);
				}
				return res.x + res.y;
			}
			
			PDX_MAIN
			{
				float2 fragCoord = Input.UV0 * SpriteSize.xy;
				float2 U = fragCoord / SpriteSize.y;
				float T = mod(GuiTime * SPEED * TAO, TAO);
				float H = clamp(.5 * sin(T) * sin(T / 2.) * exp(-T / 4.) + .5, 0., 1.);
				//float H = iTime * 0.1;
				float n = N(U, H * 5., .1) * 1.15;
				float3 C = lerp(lerp(float3(0.,0.,0.), float3(1., 0., .2), S(1., 1., n)), lerp(float3(1., 0., .2), float3(1., .635, 0.), S(.5, 1., n)), S(0., 1., n));
				
				float4 tex = SampleImageSprite( Texture, Input.UV0 );
				
				#if defined(BNW)
					float value = 1.0 - C.r;
					return float4(value, value, value, tex.a);
				#elif defined(ALPHA)
					return float4( tex.rgb, S(1., 0., n) * tex.a );
				#else
					return float4(C, tex.a);
				#endif
			}
		]]
	}
	
	MainCode PS_PODGiger
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// adapted from https://www.shadertoy.com/view/MXyXzK
			
			#define AA 2

			#define TIME GuiTime*-0.15
			#define sat(x) clamp(x, 0., 1.)
			#define screen(a, b) (1. - (1.-a) * (1.-b))
			#define nmc(x) (-cos(x)*0.5+0.5)

			#define STEEPNESS 0.8

			static float2 e = float2(0.001, 0.);

			float smin( float a, float b, float k ) {
				// iq, sigmoid
				k *= 0.301029995;//log(2.0);
				float x = b-a;
				return a + x/(1.0-exp2(x/k));
			}

			float circMap(float x) {
				return sqrt(1. - x*x);
			}

			float2 sdRidges(float2 pos) {
				pos.y *= 20.;
				float dom = 17.;
				
				float y = pos.y + sin(pos.x + TIME * 0.2 + pos.y * 0.45) * 0.5;
				y = mod(y, dom) - dom/2.;
				float effect = abs(y) / (dom/2.);
				
				float chr = effect;//abs(y) <= 1. ? 0. : 1.; // Y
				
			// float topQ = 0.3;
			
				float bumps = nmc(effect * PI * 2.) * effect;
				chr = 1.-effect;
				
				y = exp(-(-effect)*(-effect) * 10.);// * effect;
				y += bumps * 0.9;
			
				y = sat(y);
				return float2(y, chr);
			}

			float2 map(float2 pos, float2 uv) {
				float skewAngle = pos.y + TIME * 0.1 + pos.x;
				float skewAmp = 0.06;
				pos.y += sin(skewAngle) * skewAmp;
				pos.x += sin(skewAngle) * cos(skewAngle) * skewAmp * -0.5;

				float f = 20. * PI;
				float v = 0.;
				float totFalloff = 0.;
				
				float chroma = 0.;
				
				for (int i = 0; i < 3; i++) {
					float falloff = 1. / (float(i) + 1.);
					v += (
							(
								cos(pos.x * 2. * f) +
								cos(pos.y * 0.6 * f)
							)/2. * 0.5 + 0.5
						) * falloff;
					totFalloff += falloff;
					f *= 1.1;
					
					chroma += v * falloff;
				}
				v /= totFalloff;
				chroma /= totFalloff;
				v = sat(v);
				v = pow(v, 2.) * 0.3;
				
				float2 sc = sdRidges(pos);
				float2 sc2 = sdRidges(pos * float2(1., 4.)) * 0.33;
				sc = -float2(
					smin(-sc.x, -sc2.x, 0.04), // smax
					smin(-sc.y, -sc2.y, 0.04)  // smax
					);
				
				v = screen(v, sc.x * 0.6);
				
				//v = lerp(v, 1., sc.x);
				
				//chroma = screen(chroma, sc.y);
				chroma = lerp(chroma, sc.y, 0.5);
				chroma = lerp(chroma, pow(abs(uv.x * 2. - 1.) * 0.5, 0.66), 1.); // gradient from center x
				
				v = sat(v);
				return float2(v, chroma);
			}

			float2 gradient(float2 pos, float2 uv) {
				return float2(
				map(pos + e.xy, uv).x,
				map(pos + e.yx, uv).x
				) - map(pos, uv).x;
			}

			float3 normal(float2 pos, float2 uv) {
				float2 grad = gradient(pos,uv) * STEEPNESS;
				return normalize(cross(
					float3(e.x, 0., grad.x),
					float3(0., e.x, grad.y)
				));
			}

			float3 gigerPalette(float lum, float chroma) {
				const float3 dark = float3(0.05, 0.04, 0.07);
				const float3 midB = float3(0.49, 0.51, 0.58);
				//const float3 midY = float3(0.53, 0.49, 0.47);
				const float3 midY = float3(0.373,0.357,0.349);
				const float3 light = float3(0.98, 0.98, 1.00);
				
				lum = sat(lum);
				chroma = sat(chroma);
				
				float3 mid = lerp(midB, midY, chroma);
				float3 col = lum < 0.5 ? 
					lerp(dark, mid, lum * 2.) :
					lerp(mid, light, (lum - 0.5) * 2.);
				return col;
			}

			PDX_MAIN {
				float2 fragCoord = Input.UV0 * SpriteSize.xy;
				float3 avgCol = float3(0.,0.,0.);
				float2 uv = float2(0.,0.);
				float2 origPos = float2(0.,0.);
				
				for (int nn = 0; nn < AA; nn++) {
					for (int mm = 0; mm < AA; mm++) {
						float2 aa = float2(float(nn), float(mm)) / float(AA);
					
						uv = (fragCoord + aa) / SpriteSize.xy;
						uv.y = 1.0 - uv.y;
						float2 pos = (fragCoord + aa - SpriteSize.xy/2.) / SpriteSize.y * 2.;
						origPos = pos;
						pos.y -= TIME * 0.07;
						pos.x -= TIME * 0.005;
						float3 pos3 = float3(origPos, 0.);

						float2 mapped = map(pos,uv);
						float v = mapped.x;
						float chroma = mapped.y;

						float3 n = normal(pos,uv);

						float th = TIME * PI * 2. * 0.1;
						float2 timeCirc = float2(cos(th), sin(th));

						float3 lightDir = normalize(float3(timeCirc, 1.));
						float spec = max(dot(lightDir, n), 0.);

						//v = v * spec;

						float vignette = 1. - length(uv - float2(0.5,0.5)) / length(float2(0.5,0.5));
						spec = lerp(spec, lerp(spec, 1., 0.1), vignette);

						float highl = pow(v, 1.5) * 1.; // airbrush effect? bloom-ish?
						float highl2 = pow(spec, 100.);

						v *= spec * 0.5;
						v += highl + highl2; 
						v *= 0.8;

						v = pow(v, lerp(0.25, 1.5, nmc(2.0 + pos.x * 0.25)));

						float3 col = gigerPalette(v, chroma);

						vignette = pow(vignette, 1.);
						col *= lerp(0.2, 1., vignette);

						//col = float3(chroma);

						//col = float3(v);
						//col = float3(highl);
						//col = n;
						avgCol += col;
					}
				}
				avgCol /= float(AA * AA);
				
				float alpha = SampleImageSprite( Texture, Input.UV0 ).a;
				return float4(avgCol, alpha);
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

Effect PODFBM
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODFBM"
}

Effect PODFBMDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODFBM"
	Defines = { "DISABLED" }
}

Effect PODTernaryGraph
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODTernaryGraph"
}

Effect PODTernaryGraphDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODTernaryGraph"
	Defines = { "DISABLED" }
}

Effect PODYomi
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODYomi"
}

Effect PODYomiDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODYomi"
	Defines = { "DISABLED" }
}

Effect PODVeins
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
}

Effect PODVeinsDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
	Defines = { "DISABLED" }
}

Effect PODVeinsBNW
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
	Defines = { "BNW" }
}

Effect PODVeinsBNWDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
	Defines = { "BNW" "DISABLED" }
}

Effect PODVeinsAlpha
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
	Defines = { "ALPHA" }
}

Effect PODVeinsAlphaDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODVeins"
	Defines = { "ALPHA" "DISABLED" }
}

Effect PODGiger
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODGiger"
}

Effect PODGigerDisabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_PODGiger"
	Defines = { "DISABLED" }
}