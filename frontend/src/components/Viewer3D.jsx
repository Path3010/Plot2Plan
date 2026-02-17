import { Suspense } from 'react'
import { Canvas, useLoader } from '@react-three/fiber'
import { OrbitControls, Center } from '@react-three/drei'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'

function Model({ url }) {
    const gltf = useLoader(GLTFLoader, url)
    return <primitive object={gltf.scene} />
}

export default function Viewer3D({ projectId }) {
    const modelUrl = projectId ? `/api/3d-model/${projectId}` : null

    return (
        <div className="viewer-3d">
            <Canvas
                camera={{ position: [50, 50, 50], fov: 50 }}
                style={{ background: '#f8f9fc' }}
            >
                <ambientLight intensity={0.5} />
                <directionalLight position={[30, 50, 30]} intensity={1} castShadow />
                <pointLight position={[-20, 30, -20]} intensity={0.5} color="#6c5ce7" />

                <Suspense fallback={null}>
                    {modelUrl && (
                        <Center>
                            <Model url={modelUrl} />
                        </Center>
                    )}
                </Suspense>

                <OrbitControls
                    enableDamping
                    dampingFactor={0.05}
                    minDistance={10}
                    maxDistance={200}
                />

                <gridHelper args={[200, 50, '#333', '#222']} position={[0, -0.5, 0]} />
            </Canvas>
        </div>
    )
}
