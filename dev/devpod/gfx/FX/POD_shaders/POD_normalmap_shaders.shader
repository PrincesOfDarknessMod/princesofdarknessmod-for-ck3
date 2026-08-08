# adapted from https://github.com/dementive/JominiGuiPixelShaders

Includes = {
	"cw/pdxgui.fxh"
	"cw/pdxgui_sprite.fxh"
	"cw/pdxgui_sprite_base.fxh"
	"cw/pdxgui_sprite_textures.fxh"
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

	MainCode PS_REFRACTION01
	{
		Input = "VS_OUTPUT_PDX_GUI"
		Output = "PDX_COLOR"
		Code
		[[
			// somewhat based on https://www.shadertoy.com/view/MsySWK
			
			float calcLatitude(in float3 pos) {
				return acos( pos.z / sqrt( pos.x * pos.x + pos.y * pos.y + pos.z * pos.z ) );
			}
			
			float calcLongitude(in float3 pos) {
				return acos( pos.x / sqrt( pos.x * pos.x + pos.y * pos.y ) );
			}
			
			float2 vecToEquidistantUV(in float3 pos) {
				float x = calcLongitude(pos) / PI;
				float y = calcLatitude(pos) / PI;
				return float2( x, y );
			}
			
			// Compact, self-contained version of IQ's 3D value noise function.
			float n3D(float3 p){
				
				const float3 s = float3(7, 157, 113);
				float3 ip = floor(p); p -= ip; 
				float4 h = float4(0., s.yz, s.y + s.z) + dot(ip, s);
				p = p*p*(3. - 2.*p); //p *= p*p*(p*(p * 6. - 15.) + 10.);
				h = lerp(frac(sin(h)*43758.5453), frac(sin(h + s.x)*43758.5453), p.x);
				h.xy = lerp(h.xz, h.yw, p.y);
				return lerp(h.x, h.y, p.z); // Range: [0, 1].
			}

			// Simple environment mapping. Pass the reflected vector in and create some
			// colored noise with it. The normal is redundant here, but it can be used
			// to pass into a 3D texture mapping function to produce some interesting
			// environmental reflections.
			float3 envMap(float3 rd, float3 sn){
				
				float3 sRd = rd; // Save rd, just for some mixing at the end.
				
				// Add a time component, scale, then pass into the noise function.
				rd.xy -= GuiTime*.1;
				rd *= 3.;
				
				float c = n3D(rd)*.57 + n3D(rd*2.)*.28 + n3D(rd*4.)*.15; // Noise value.
				c = smoothstep(0.4, 1., c); // Darken and add contast for more of a spotlight look.
				
				float3 col = float3(c, c*c, c*c*c*c); // Simple, warm coloring.
				//float3 col = float3(min(c*1.5, 1.), pow(c, 2.5), pow(c, 12.)); // More color.
				
				// Mix in some more red to tone it down and return.
				return lerp(col, col.yzx, sRd*.25+.25);
				//return col;
			}

			float3 rot3dX(in float3 coord, in float angle) {
				float c = cos(angle);
				float s = sin(angle);
				return mul( coord, float3x3(
					float3(1, 0, 0),
					float3(0, c, -s),
					float3(0, s, c)
				) );
			}
			
			float3 rotate4Cubemap(float3 pos) {
				float3 dir = pos;
				dir = rot3dX(dir, PI*0.4);
				return dir;
			}

			PDX_MAIN {
				float2 uv = Input.UV0;
				uv.x = 1.0 - uv.x;
				
				float2 fragCoord = uv * SpriteSize.xy;
				
				float3 normal = normalize(PdxTex2D(Texture, uv).rgb);
				
				// Ray origin
				float3 ro = float3(1.0, 1.0, 1.0);
				
				// Surface postion
				float3 sp = float3(uv,0.);
				
				// Ray direction
				float3 rd = normalize( sp - ro );
				
				// Light position
				//float3 lp = ro + float3(cos(GuiTime/2.)*.5, sin(GuiTime/2.)*.5, -.5);
				float2 lp2d = 0.5 + 1.4 * float2(cos(GuiTime*.2), sin(GuiTime*.2));
				//float3 lp = ro + float3(lp2d, 1.0);
				float3 lp = ro + float3(0.0 + 0.25 * cos(GuiTime*0.5), -0.5, 0.5);
				
				// Point light
				float3 ld = lp - sp; // Light direction vector.
				float lDist = max(length(ld), 0.001); // Light distance.
				float atten = 1./(1. + lDist*lDist*.125); // Light attenuation.
				ld /= lDist; // Normalizing the light direction vector.
				
				float diff = max(dot(ld, normal), 0.); // Diffuse.
				diff = pow(diff,20.);
				float spec = pow(max( dot( reflect(-ld, normal), -rd ), 0.0 ), 32.); // Specular.
				float fre = clamp(dot(normal, rd) + 1., .0, 1.); // Fake fresnel, for the glow.
				
				// Combining the terms above to light the texel
				//float3 col = diff + float3(1, .7, .3)*spec + float3(.1, .3, 1)*pow(fre, 2.)*8.;
				//float3 col = float3(0.6, 0.9, 1.0)*diff + float3(0., .8, .9)*spec + float3(.1, .3, 1)*pow(fre, 3.)*8.;
				//float3 col = float3(1.0, 0.9, 0.7)*diff + float3(0., .6, .7)*spec + float3(.1, .3, 1)*pow(fre, 3.)*8.;
				//float3 col = float3(1.0, 0.9, 0.7)*diff + float3(0., .6, .7)*spec + float3(1., .0, .0)*pow(fre, 3.)*48.;
				float3 col = SpriteModifyTexturesColors[2].rgb*diff + SpriteModifyTexturesColors[3].rgb*spec + SpriteModifyTexturesColors[4].rgb*pow(fre, SpriteBorder[4].x)*SpriteBorder[4].y;
				
				float3 cubeDir = rotate4Cubemap(reflect(rd, normal));
				
				float3 cube = PdxTex2D(ModifyTexture0, vecToEquidistantUV(cubeDir)).rgb;
				cube = sqrt(cube);
				col *= cube;
				
				float3 env = envMap(reflect(ld, normal), normal)*2.*(1.0-uv.y);
				//col += sqrt(env);
				col = lerp(col,col*env*env,env.r);
				
				// Applying the shades.
				//col *= (atten*crv*ao);
				col *= atten;
				
				// Vignette.
				col *= pow(16.*uv.x*uv.y*(1.-uv.x)*(1.-uv.y), 0.125);

				// Presenting to the screen.
				float alpha = SampleImageSprite(Texture,Input.UV0).a;
				return float4(sqrt(clamp(col, 0., 1.)), alpha);
				//return float4(cube, alpha);
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

Effect PODNormalRefraction01
{
	VertexShader = "VS_Default"
	PixelShader = "PS_REFRACTION01"
}
Effect PODNormalRefraction01Disabled
{
	VertexShader = "VS_Default"
	PixelShader = "PS_REFRACTION01"
	
	Defines = { "DISABLED" }
}