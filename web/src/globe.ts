import {
  Cartesian3,
  Color,
  EllipsoidTerrainProvider,
  ImageryLayer,
  Math as CesiumMath,
  SkyAtmosphere,
  UrlTemplateImageryProvider,
  Viewer,
  WebMercatorTilingScheme,
} from 'cesium';
import type { SpeciesRecord } from './search';

export class AquaticGlobe {
  readonly viewer: Viewer;
  private heatLayer: ImageryLayer | null = null;

  private constructor(viewer: Viewer) {
    this.viewer = viewer;
  }

  static create(container: HTMLElement): AquaticGlobe {
    const viewer = new Viewer(container, {
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      creditContainer: document.createElement('div'),
      showRenderLoopErrors: false,
      terrainProvider: new EllipsoidTerrainProvider(),
      baseLayer: false,
      skyAtmosphere: new SkyAtmosphere(),
    });

    const globeView = new AquaticGlobe(viewer);
    globeView.configureScene();
    globeView.addBaseImagery();
    return globeView;
  }

  /** Esri World Imagery base map — free, no API key, gives the Google-Earth look. */
  private addBaseImagery(): void {
    const provider = new UrlTemplateImageryProvider({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      tilingScheme: new WebMercatorTilingScheme(),
      minimumLevel: 0,
      maximumLevel: 18,
      credit: 'Esri, Maxar, Earthstar Geographics',
    });
    this.viewer.imageryLayers.addImageryProvider(provider);
  }

  private configureScene(): void {
    const { scene } = this.viewer;
    const globe = scene.globe;
    if (scene.skyAtmosphere) scene.skyAtmosphere.show = true;
    scene.fog.enabled = true;
    scene.fog.density = 0.00015;
    globe.enableLighting = true;
    globe.depthTestAgainstTerrain = false;
    globe.baseColor = Color.fromCssColorString('#8fc3e4');
    globe.showGroundAtmosphere = true;
    globe.atmosphereLightIntensity = 18;
    globe.atmosphereRayleighCoefficient = new Cartesian3(0.005, 0.018, 0.045);

    this.viewer.camera.setView({
      destination: Cartesian3.fromDegrees(-118.5, 33.5, 4_500_000),
      orientation: {
        heading: CesiumMath.toRadians(0),
        pitch: CesiumMath.toRadians(-55),
        roll: 0,
      },
    });
  }

  async flyToSpecies(species: SpeciesRecord): Promise<void> {
    const { lat, lon } = species.centroid;
    await this.viewer.camera.flyTo({
      destination: Cartesian3.fromDegrees(lon, lat, 1_800_000),
      duration: 2.4,
      easingFunction: (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2),
    });
  }

  setHeatmap(species: SpeciesRecord | null, fadeIn = true): void {
    if (this.heatLayer) {
      this.viewer.imageryLayers.remove(this.heatLayer, false);
      this.heatLayer = null;
    }
    if (!species) return;

    const provider = new UrlTemplateImageryProvider({
      url: `/tiles/${species.slug}/{z}/{x}/{y}.webp`,
      minimumLevel: 0,
      maximumLevel: 6,
      tilingScheme: new WebMercatorTilingScheme(),
      credit: 'AquaMaps illustrative range',
    });

    const layer = this.viewer.imageryLayers.addImageryProvider(provider);
    layer.alpha = fadeIn ? 0 : 0.82;
    this.heatLayer = layer;

    if (fadeIn) {
      const start = performance.now();
      const duration = 900;
      const tick = (now: number) => {
        const t = Math.min(1, (now - start) / duration);
        layer.alpha = 0.82 * t;
        if (t < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }
  }
}
