Includes = {
	"cw/camera.fxh"
	"jomini/jomini.fxh"
}

Code
[[
	float CalculateDistanceFogFactor( float3 WorldSpacePos )
	{
		float3 Diff = CameraPosition - WorldSpacePos;
		float vFogFactor = 1.0 - abs( normalize( Diff ).y ); // abs b/c of reflections
		float vSqDistance = dot( Diff, Diff );

		float vMin = min( ( vSqDistance - FogBegin2 ) / ( FogEnd2 - FogBegin2 ), FogMax );
		return saturate( vMin * vFogFactor );
	}

	float3 ApplyDistanceFog( float3 Color, float vFogFactor )
	{
		return lerp( Color, FogColor, vFogFactor );
	}

	float3 ApplyDistanceFog( float3 Color, float3 WorldSpacePos )
	{
		return ApplyDistanceFog( Color, CalculateDistanceFogFactor( WorldSpacePos ) );
	}
]]