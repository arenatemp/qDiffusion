import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

import gui 1.0

TabButton {
    id: control
    width: implicitWidth
    property var selected: false


    contentItem: Item {

    }

    background: Item {
        implicitHeight: 40
        implicitWidth: 100
        Rectangle {
            height: 25
            opacity: enabled ? 1 : 0.3
            color: control.down ? COMMON.bg0 : (selected ? COMMON.bg4 : COMMON.bg2)
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            clip:true
            Rectangle {
                rotation: 20
                width: parent.height
                height:  2*parent.height
                x: -width
                y: -parent.height
                transformOrigin: Item.BottomRight
                antialiasing: true
                color: COMMON.bg3
            }

            Rectangle {
                rotation: -20
                width: parent.height
                height:  2*parent.height
                x: parent.width+2
                y: -parent.height
                transformOrigin: Item.BottomRight
                antialiasing: true
                color: COMMON.bg3
            }

            SText {
                anchors.fill: parent
                topPadding: 1
                text: control.text
                font.pointSize: 10.9
                opacity: enabled ? 1.0 : 0.3
                color: COMMON.fg0
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment:  Text.AlignVCenter
                elide: Text.ElideRight
            }
        }
    }
}