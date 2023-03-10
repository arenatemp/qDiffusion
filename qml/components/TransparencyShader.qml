	
import QtQuick 2.0

Item {
    property real gridSize: 10.0
    ShaderEffect {
        property real gridSize: parent.gridSize
        anchors.fill: parent
        vertexShader: "
            uniform highp mat4 qt_Matrix;
            attribute highp vec4 qt_Vertex;
            attribute highp vec2 qt_MultiTexCoord0;
            varying highp vec2 coord;
            void main() {
                coord = qt_Vertex.xy;
                gl_Position = qt_Matrix * qt_Vertex;
            }"
        fragmentShader: "
            varying highp vec2 coord;
            uniform float gridSize;
            void main() {
                vec2 pos = floor(coord / gridSize);
                gl_FragColor.xyz = vec3(0.2, 0.2, 0.2) + mod(pos.x + mod(pos.y, 2.0), 2.0) * 0.2;
                gl_FragColor.w = 1.0;
            }"
    }
}