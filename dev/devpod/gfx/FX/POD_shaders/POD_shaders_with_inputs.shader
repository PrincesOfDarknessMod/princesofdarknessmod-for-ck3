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