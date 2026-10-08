Includes = {
	"pdxmesh_vfx.fxh"
	"ssao_struct.fxh"
}

PixelShader =
{
	TextureSampler DiffuseMap
	{
		Index = 0
		MagFilter = "Linear"
		MinFilter = "Linear"
		MipFilter = "Linear"
		SampleModeU = "Wrap"
		SampleModeV = "Wrap"
	}
}

# halo should be behind the existing portrait
BlendState halo_behind_portrait_blend
{
	BlendEnable = yes
	SourceBlend = "INV_DEST_ALPHA"
	DestBlend = "ONE"
	SourceAlpha = "ONE"
	DestAlpha = "INV_SRC_ALPHA"
	WriteMask = "RED|GREEN|BLUE|ALPHA"
}

DepthStencilState depth_no_write
{
	DepthEnable = yes
	DepthWriteEnable = no
}

RasterizerState rasterizer_no_culling
{
	CullMode = "none"
}

Effect mesh_vfx_head_halo
{
	VertexShader = "VS_mesh_vfx_standard"
	PixelShader = "PS_mesh_vfx_head_halo"
	BlendState = "halo_behind_portrait_blend"
	DepthStencilState = "depth_no_write"
	RasterizerState = "rasterizer_no_culling"
	Defines = { "BILLBOARD_HALO_MESH" "BILLBOARD_OFFSET_DISTANCE 30.0"}	
}
