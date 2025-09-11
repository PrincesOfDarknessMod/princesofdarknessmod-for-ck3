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